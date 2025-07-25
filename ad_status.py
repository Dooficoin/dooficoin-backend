from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.ad_manager import AdManager
from utils.security import log_security_event

ad_status_bp = Blueprint('ad_status', __name__)

@ad_status_bp.route('/status/<int:display_id>', methods=['GET'])
def get_ad_status(display_id):
    """Obtém o status atual de um anúncio exibido."""
    try:
        # Usar AdManager para obter o status
        result = AdManager.get_ad_status(display_id)
        
        if not result['found']:
            return jsonify({'error': result['error']}), 404
        
        return jsonify({
            'status': result['status'],
            'can_close': result['can_close'],
            'seconds_remaining': result['seconds_remaining'],
            'protection_end_time': result['protection_end_time'],
            'display': result['display']
        })
    
    except Exception as e:
        log_security_event('ad_status_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving ad status'}), 500

@ad_status_bp.route('/check-availability/<placement>', methods=['GET'])
def check_ad_availability(placement):
    """Verifica se um anúncio pode ser exibido sem criar o registro."""
    try:
        # Obter informações da requisição
        session_id = request.headers.get('X-Session-ID', f'anonymous_{datetime.utcnow().timestamp()}')
        ip_address = request.remote_addr
        
        # Verificar se o usuário está logado (implementação básica)
        player_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # Aqui você implementaria a verificação do token
            # Por simplicidade, vamos deixar como None por enquanto
            pass
        
        # Verificar disponibilidade
        check_result = AdManager.can_show_ad(placement, session_id, ip_address, player_id)
        
        return jsonify({
            'available': check_result['can_show'],
            'reason': check_result.get('reason'),
            'retry_after': check_result.get('retry_after'),
            'seconds_remaining': check_result.get('seconds_remaining')
        })
    
    except Exception as e:
        log_security_event('ad_availability_check_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while checking ad availability'}), 500

@ad_status_bp.route('/countdown/<int:display_id>', methods=['GET'])
def get_ad_countdown(display_id):
    """Obtém informações de countdown para um anúncio específico."""
    try:
        # Usar AdManager para obter o status
        result = AdManager.get_ad_status(display_id)
        
        if not result['found']:
            return jsonify({'error': result['error']}), 404
        
        # Calcular informações de countdown
        now = datetime.utcnow()
        display_data = result['display']
        
        # Tempo desde que o anúncio foi exibido
        displayed_at = datetime.fromisoformat(display_data['displayed_at'].replace('Z', '+00:00'))
        elapsed_seconds = int((now - displayed_at).total_seconds())
        
        # Tempo total de proteção
        protection_seconds = result['seconds_remaining'] + elapsed_seconds if not result['can_close'] else elapsed_seconds
        
        return jsonify({
            'display_id': display_id,
            'status': result['status'],
            'can_close': result['can_close'],
            'seconds_remaining': result['seconds_remaining'],
            'elapsed_seconds': elapsed_seconds,
            'total_protection_seconds': protection_seconds,
            'progress_percentage': min(100, (elapsed_seconds / protection_seconds) * 100) if protection_seconds > 0 else 100
        })
    
    except Exception as e:
        log_security_event('ad_countdown_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving ad countdown'}), 500

