from flask import Blueprint, jsonify, request
from models.user import User, db
from models.security_log import LoginAttempt
from utils.security import is_valid_email, is_valid_username, sanitize_input, check_login_attempts, generate_token, log_security_event

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.json
    
    # Validar e sanitizar entradas
    username = sanitize_input(data.get('username'))
    email = sanitize_input(data.get('email'))
    
    if not username or not email:
        return jsonify({'error': 'Username and email are required'}), 400
    
    if not is_valid_username(username):
        return jsonify({'error': 'Invalid username format. Use 3-20 alphanumeric characters, underscores, or hyphens.'}), 400
    
    if not is_valid_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Verificar se o usuário ou email já existem
    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        log_security_event('user_registration_duplicate', 
                          f'Attempted to register with existing username/email: {username}/{email}', 
                          'warning')
        return jsonify({'error': 'Username or email already exists'}), 409
    
    # Criar o novo usuário
    user = User(username=username, email=email)
    db.session.add(user)
    db.session.commit()
    
    log_security_event('user_created', f'New user created: {username}', 'info')
    
    return jsonify(user.to_dict()), 201

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    
    # Validar e sanitizar entradas
    username = sanitize_input(data.get('username', user.username))
    email = sanitize_input(data.get('email', user.email))
    
    if username != user.username and not is_valid_username(username):
        return jsonify({'error': 'Invalid username format. Use 3-20 alphanumeric characters, underscores, or hyphens.'}), 400
    
    if email != user.email and not is_valid_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Verificar se o novo username ou email já existem
    if username != user.username or email != user.email:
        existing_user = User.query.filter(
            ((User.username == username) | (User.email == email)) & 
            (User.id != user_id)
        ).first()
        
        if existing_user:
            log_security_event('user_update_duplicate', 
                              f'Attempted to update to existing username/email: {username}/{email}', 
                              'warning',
                              user_id=user_id)
            return jsonify({'error': 'Username or email already exists'}), 409
    
    # Atualizar o usuário
    user.username = username
    user.email = email
    db.session.commit()
    
    log_security_event('user_updated', 
                      f'User {user_id} updated: username={username}, email={email}', 
                      'info',
                      user_id=user_id)
    
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    log_security_event('user_deleted', 
                      f'User {user_id} ({user.username}) deleted', 
                      'warning',
                      user_id=user_id)
    
    db.session.delete(user)
    db.session.commit()
    return '', 204

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username_or_email = sanitize_input(data.get('username'))
    password = data.get('password', '')  # Não sanitizar senhas, pois podem conter caracteres especiais
    
    if not username_or_email:
        return jsonify({'error': 'Username or email is required'}), 400
    
    # Verificar tentativas de login para este IP
    client_ip = request.remote_addr
    can_attempt, wait_time = check_login_attempts(client_ip)
    
    if not can_attempt:
        # Registrar tentativa bloqueada
        login_attempt = LoginAttempt(
            ip_address=client_ip,
            username=username_or_email,
            success=False,
            user_agent=request.headers.get('User-Agent', '')
        )
        db.session.add(login_attempt)
        db.session.commit()
        
        log_security_event('login_blocked', 
                          f'Login blocked for IP {client_ip} due to too many failed attempts', 
                          'warning')
        
        return jsonify({
            'error': 'Too many failed login attempts',
            'wait_time': wait_time
        }), 429
    
    # Buscar o usuário
    user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
    
    # Em um sistema real, verificaríamos a senha aqui
    # Por enquanto, simulamos um login bem-sucedido se o usuário existir
    if user:
        # Registrar login bem-sucedido
        login_attempt = LoginAttempt(
            ip_address=client_ip,
            username=username_or_email,
            success=True,
            user_agent=request.headers.get('User-Agent', '')
        )
        db.session.add(login_attempt)
        db.session.commit()
        
        # Limpar tentativas de login para este IP
        check_login_attempts(client_ip, success=True)
        
        # Gerar token JWT
        token = generate_token(user.id, is_admin=getattr(user, 'is_admin', False))
        
        log_security_event('login_success', 
                          f'User {user.username} logged in successfully', 
                          'info',
                          user_id=user.id)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'token': token
        })
    else:
        # Registrar tentativa falha
        login_attempt = LoginAttempt(
            ip_address=client_ip,
            username=username_or_email,
            success=False,
            user_agent=request.headers.get('User-Agent', '')
        )
        db.session.add(login_attempt)
        db.session.commit()
        
        log_security_event('login_failed', 
                          f'Failed login attempt for username/email: {username_or_email}', 
                          'warning')
        
        return jsonify({'error': 'Invalid username/email or password'}), 401

