import re
import time
import hashlib
import ipaddress
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app

# Dicionário para armazenar tentativas de login por IP
login_attempts = {}
# Dicionário para armazenar IPs bloqueados
blocked_ips = {}
# Dicionário para armazenar contagem de requisições por IP (para rate limiting)
request_counts = {}

def is_valid_email(email):
    """Valida se o email está em um formato correto."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_username(username):
    """Valida se o nome de usuário contém apenas caracteres permitidos."""
    pattern = r'^[a-zA-Z0-9_-]{3,20}$'
    return bool(re.match(pattern, username))

def is_valid_password(password):
    """
    Valida se a senha atende aos requisitos mínimos de segurança:
    - Pelo menos 8 caracteres
    - Pelo menos uma letra maiúscula
    - Pelo menos uma letra minúscula
    - Pelo menos um número
    - Pelo menos um caractere especial
    """
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

def sanitize_input(input_str):
    """Sanitiza a entrada do usuário para prevenir injeções."""
    if input_str is None:
        return None
    # Remove caracteres potencialmente perigosos
    sanitized = re.sub(r'[<>\'";]', '', input_str)
    return sanitized

def generate_token(user_id, is_admin=False, expiration_hours=24):
    """Gera um token JWT para autenticação."""
    payload = {
        'user_id': user_id,
        'is_admin': is_admin,
        'exp': datetime.utcnow() + timedelta(hours=expiration_hours)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    """Verifica se um token JWT é válido."""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator para rotas que requerem autenticação por token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Verificar se o token está no header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        # Adicionar o payload do token ao request para uso na função decorada
        request.token_payload = payload
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator para rotas que requerem privilégios de administrador."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Verificar se o token está no header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        # Verificar se o usuário é um administrador
        if not payload.get('is_admin', False):
            return jsonify({'error': 'Admin privileges required'}), 403
        
        # Adicionar o payload do token ao request para uso na função decorada
        request.token_payload = payload
        
        return f(*args, **kwargs)
    
    return decorated

def rate_limit(max_requests=10, window_seconds=60):
    """
    Decorator para limitar o número de requisições por IP em um período de tempo.
    Por padrão, limita a 10 requisições por minuto.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Obter o IP do cliente
            client_ip = request.remote_addr
            
            # Verificar se o IP está bloqueado
            if client_ip in blocked_ips:
                block_until = blocked_ips[client_ip]
                if time.time() < block_until:
                    return jsonify({'error': 'Too many requests. Try again later.'}), 429
                else:
                    # Remover o IP da lista de bloqueados se o tempo expirou
                    del blocked_ips[client_ip]
            
            # Inicializar contagem para este IP se não existir
            if client_ip not in request_counts:
                request_counts[client_ip] = []
            
            # Remover timestamps antigos
            current_time = time.time()
            request_counts[client_ip] = [t for t in request_counts[client_ip] if current_time - t < window_seconds]
            
            # Verificar se o limite foi atingido
            if len(request_counts[client_ip]) >= max_requests:
                # Bloquear o IP por 5 minutos
                blocked_ips[client_ip] = current_time + 300  # 5 minutos em segundos
                return jsonify({'error': 'Rate limit exceeded. Try again later.'}), 429
            
            # Adicionar o timestamp atual
            request_counts[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator

def check_login_attempts(ip_address, success=False):
    """
    Verifica e registra tentativas de login por IP.
    Bloqueia o IP após 5 tentativas falhas em 15 minutos.
    """
    current_time = time.time()
    
    # Inicializar registro para este IP se não existir
    if ip_address not in login_attempts:
        login_attempts[ip_address] = {'attempts': [], 'blocked_until': None}
    
    # Verificar se o IP está bloqueado
    if login_attempts[ip_address]['blocked_until'] and current_time < login_attempts[ip_address]['blocked_until']:
        return False, login_attempts[ip_address]['blocked_until'] - current_time
    
    # Limpar o bloqueio se expirou
    if login_attempts[ip_address]['blocked_until'] and current_time >= login_attempts[ip_address]['blocked_until']:
        login_attempts[ip_address]['blocked_until'] = None
    
    # Se o login foi bem-sucedido, limpar as tentativas
    if success:
        login_attempts[ip_address]['attempts'] = []
        return True, 0
    
    # Remover tentativas antigas (mais de 15 minutos)
    login_attempts[ip_address]['attempts'] = [t for t in login_attempts[ip_address]['attempts'] if current_time - t < 900]
    
    # Adicionar nova tentativa
    login_attempts[ip_address]['attempts'].append(current_time)
    
    # Verificar se atingiu o limite de tentativas
    if len(login_attempts[ip_address]['attempts']) >= 5:
        # Bloquear por 30 minutos
        block_time = 1800  # 30 minutos em segundos
        login_attempts[ip_address]['blocked_until'] = current_time + block_time
        login_attempts[ip_address]['attempts'] = []
        return False, block_time
    
    return True, 0

def is_ip_in_blacklist(ip_address):
    """Verifica se um IP está em uma lista negra (simulada)."""
    # Lista de IPs conhecidos por atividades maliciosas (simulada)
    blacklist = [
        '1.2.3.4',
        '5.6.7.8',
        # Adicionar mais IPs conforme necessário
    ]
    
    return ip_address in blacklist

def log_security_event(event_type, details, severity='info'):
    """
    Registra eventos de segurança para análise posterior.
    Severidade pode ser: 'info', 'warning', 'error', 'critical'
    """
    # Em um ambiente de produção, isso seria salvo em um banco de dados ou sistema de log
    event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'details': details,
        'severity': severity,
        'ip_address': request.remote_addr if request else 'unknown'
    }
    
    # Por enquanto, apenas imprimimos o evento
    print(f"SECURITY EVENT: {event}")
    
    # Em um ambiente real, você poderia enviar alertas para eventos críticos
    if severity == 'critical':
        # Enviar alerta (e-mail, SMS, etc.)
        pass
    
    return event

