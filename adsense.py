from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json
from decimal import Decimal
from models.user import db
from models.adsense import AdSenseConfig, AdUnit, AdDisplay, AdRevenue
from utils.security import token_required, log_security_event
from utils.ad_manager import AdManager

adsense_bp = Blueprint('adsense', __name__)

# URLs da API do Google AdSense
GOOGLE_OAUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
ADSENSE_API_BASE = 'https://www.googleapis.com/adsense/v2'

@adsense_bp.route('/config', methods=['GET'])
@token_required
def get_adsense_config():
    """Obtém a configuração atual do AdSense."""
    try:
        config = AdSenseConfig.query.first()
        
        if not config:
            return jsonify({
                'configured': False,
                'message': 'AdSense not configured yet'
            })
        
        return jsonify({
            'configured': True,
            'config': config.to_dict()
        })
    
    except Exception as e:
        log_security_event('adsense_config_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving AdSense configuration'}), 500

@adsense_bp.route('/config', methods=['POST'])
@token_required
def create_adsense_config():
    """Cria ou atualiza a configuração do AdSense."""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['publisher_id', 'client_id', 'client_secret']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Verificar se já existe uma configuração
        config = AdSenseConfig.query.first()
        
        if config:
            # Atualizar configuração existente
            config.publisher_id = data['publisher_id']
            config.client_id = data['client_id']
            config.client_secret = data['client_secret']
            config.updated_at = datetime.utcnow()
            
            # Atualizar configurações de anúncios se fornecidas
            if 'ad_settings' in data:
                config.ad_settings = json.dumps(data['ad_settings'])
        else:
            # Criar nova configuração
            config = AdSenseConfig(
                publisher_id=data['publisher_id'],
                client_id=data['client_id'],
                client_secret=data['client_secret'],
                ad_settings=json.dumps(data.get('ad_settings', {}))
            )
            db.session.add(config)
        
        db.session.commit()
        
        log_security_event('adsense_config_updated', 
                          f'AdSense configuration updated for publisher {config.publisher_id}', 
                          'info')
        
        return jsonify({
            'message': 'AdSense configuration saved successfully',
            'config': config.to_dict()
        })
    
    except Exception as e:
        log_security_event('adsense_config_create_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while saving AdSense configuration'}), 500

@adsense_bp.route('/oauth/authorize', methods=['GET'])
@token_required
def authorize_adsense():
    """Inicia o processo de autorização OAuth com o Google AdSense."""
    try:
        config = AdSenseConfig.query.first()
        
        if not config:
            return jsonify({'error': 'AdSense configuration not found'}), 404
        
        # Parâmetros para autorização OAuth
        oauth_params = {
            'client_id': config.client_id,
            'redirect_uri': url_for('adsense.oauth_callback', _external=True),
            'scope': 'https://www.googleapis.com/auth/adsense.readonly',
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        # Gerar URL de autorização
        auth_url = f"{GOOGLE_OAUTH_URL}?{urlencode(oauth_params)}"
        
        return jsonify({
            'authorization_url': auth_url,
            'message': 'Please visit the authorization URL to grant access'
        })
    
    except Exception as e:
        log_security_event('adsense_oauth_authorize_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while generating authorization URL'}), 500

@adsense_bp.route('/oauth/callback')
def oauth_callback():
    """Callback para processar a resposta da autorização OAuth."""
    try:
        # Obter o código de autorização
        auth_code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            log_security_event('adsense_oauth_error', f'OAuth error: {error}', 'error')
            return jsonify({'error': f'OAuth authorization failed: {error}'}), 400
        
        if not auth_code:
            return jsonify({'error': 'Authorization code not received'}), 400
        
        config = AdSenseConfig.query.first()
        
        if not config:
            return jsonify({'error': 'AdSense configuration not found'}), 404
        
        # Trocar o código de autorização por tokens de acesso
        token_data = {
            'client_id': config.client_id,
            'client_secret': config.client_secret,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': url_for('adsense.oauth_callback', _external=True)
        }
        
        response = requests.post(GOOGLE_TOKEN_URL, data=token_data)
        response.raise_for_status()
        
        token_info = response.json()
        
        # Atualizar a configuração com os tokens
        config.update_tokens(
            access_token=token_info['access_token'],
            refresh_token=token_info.get('refresh_token'),
            expires_in=token_info.get('expires_in', 3600)
        )
        
        config.is_active = True
        db.session.commit()
        
        log_security_event('adsense_oauth_success', 
                          f'AdSense OAuth authorization successful for publisher {config.publisher_id}', 
                          'info')
        
        return jsonify({
            'message': 'AdSense authorization successful',
            'config': config.to_dict()
        })
    
    except Exception as e:
        log_security_event('adsense_oauth_callback_error', str(e), 'error')
        return jsonify({'error': 'An error occurred during OAuth callback'}), 500

@adsense_bp.route('/refresh-token', methods=['POST'])
@token_required
def refresh_access_token():
    """Renova o token de acesso do AdSense."""
    try:
        config = AdSenseConfig.query.first()
        
        if not config or not config.refresh_token:
            return jsonify({'error': 'No refresh token available'}), 400
        
        # Renovar o token de acesso
        token_data = {
            'client_id': config.client_id,
            'client_secret': config.client_secret,
            'refresh_token': config.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(GOOGLE_TOKEN_URL, data=token_data)
        response.raise_for_status()
        
        token_info = response.json()
        
        # Atualizar a configuração com o novo token
        config.update_tokens(
            access_token=token_info['access_token'],
            expires_in=token_info.get('expires_in', 3600)
        )
        
        log_security_event('adsense_token_refreshed', 
                          f'AdSense token refreshed for publisher {config.publisher_id}', 
                          'info')
        
        return jsonify({
            'message': 'Access token refreshed successfully',
            'config': config.to_dict()
        })
    
    except Exception as e:
        log_security_event('adsense_token_refresh_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while refreshing access token'}), 500

@adsense_bp.route('/ad-units', methods=['GET'])
@token_required
def get_ad_units():
    """Lista todas as unidades de anúncio configuradas."""
    try:
        ad_units = AdUnit.query.all()
        
        return jsonify({
            'ad_units': [unit.to_dict() for unit in ad_units]
        })
    
    except Exception as e:
        log_security_event('adsense_ad_units_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving ad units'}), 500

@adsense_bp.route('/ad-units', methods=['POST'])
@token_required
def create_ad_unit():
    """Cria uma nova unidade de anúncio."""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['unit_id', 'unit_name', 'ad_type', 'placement']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Verificar se existe configuração do AdSense
        config = AdSenseConfig.query.first()
        if not config:
            return jsonify({'error': 'AdSense configuration not found'}), 404
        
        # Criar nova unidade de anúncio
        ad_unit = AdUnit(
            adsense_config_id=config.id,
            unit_id=data['unit_id'],
            unit_name=data['unit_name'],
            ad_type=data['ad_type'],
            placement=data['placement'],
            unit_settings=json.dumps(data.get('unit_settings', {}))
        )
        
        db.session.add(ad_unit)
        db.session.commit()
        
        log_security_event('adsense_ad_unit_created', 
                          f'Ad unit created: {ad_unit.unit_name} ({ad_unit.placement})', 
                          'info')
        
        return jsonify({
            'message': 'Ad unit created successfully',
            'ad_unit': ad_unit.to_dict()
        }), 201
    
    except Exception as e:
        log_security_event('adsense_ad_unit_create_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while creating ad unit'}), 500

@adsense_bp.route('/ad-units/<int:unit_id>', methods=['PUT'])
@token_required
def update_ad_unit(unit_id):
    """Atualiza uma unidade de anúncio existente."""
    try:
        ad_unit = AdUnit.query.get(unit_id)
        
        if not ad_unit:
            return jsonify({'error': 'Ad unit not found'}), 404
        
        data = request.get_json()
        
        # Atualizar campos permitidos
        if 'unit_name' in data:
            ad_unit.unit_name = data['unit_name']
        if 'ad_type' in data:
            ad_unit.ad_type = data['ad_type']
        if 'placement' in data:
            ad_unit.placement = data['placement']
        if 'is_active' in data:
            ad_unit.is_active = data['is_active']
        if 'unit_settings' in data:
            ad_unit.unit_settings = json.dumps(data['unit_settings'])
        
        ad_unit.updated_at = datetime.utcnow()
        db.session.commit()
        
        log_security_event('adsense_ad_unit_updated', 
                          f'Ad unit updated: {ad_unit.unit_name}', 
                          'info')
        
        return jsonify({
            'message': 'Ad unit updated successfully',
            'ad_unit': ad_unit.to_dict()
        })
    
    except Exception as e:
        log_security_event('adsense_ad_unit_update_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while updating ad unit'}), 500

@adsense_bp.route('/ad-units/<int:unit_id>', methods=['DELETE'])
@token_required
def delete_ad_unit(unit_id):
    """Remove uma unidade de anúncio."""
    try:
        ad_unit = AdUnit.query.get(unit_id)
        
        if not ad_unit:
            return jsonify({'error': 'Ad unit not found'}), 404
        
        unit_name = ad_unit.unit_name
        db.session.delete(ad_unit)
        db.session.commit()
        
        log_security_event('adsense_ad_unit_deleted', 
                          f'Ad unit deleted: {unit_name}', 
                          'info')
        
        return jsonify({
            'message': 'Ad unit deleted successfully'
        })
    
    except Exception as e:
        log_security_event('adsense_ad_unit_delete_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while deleting ad unit'}), 500

@adsense_bp.route('/display/<placement>', methods=['GET'])
def get_ad_for_placement(placement):
    """Obtém um anúncio para exibir em um local específico."""
    try:
        # Obter informações da requisição
        session_id = request.headers.get('X-Session-ID', f'anonymous_{datetime.utcnow().timestamp()}')
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Verificar se o usuário está logado (implementação básica)
        player_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # Aqui você implementaria a verificação do token
            # Por simplicidade, vamos deixar como None por enquanto
            pass
        
        # Verificar se o anúncio pode ser exibido
        check_result = AdManager.can_show_ad(placement, session_id, ip_address, player_id)
        
        if not check_result['can_show']:
            return jsonify({
                'ad_available': False,
                'reason': check_result['reason'],
                'retry_after': check_result.get('retry_after'),
                'seconds_remaining': check_result.get('seconds_remaining')
            })
        
        # Criar registro de exibição do anúncio
        ad_display = AdManager.create_ad_display(
            check_result['ad_unit'], 
            session_id, 
            ip_address, 
            user_agent, 
            player_id
        )
        
        return jsonify({
            'ad_available': True,
            'ad_display': ad_display.to_dict(),
            'ad_unit': check_result['ad_unit'].to_dict(),
            'publisher_id': check_result['config'].publisher_id,
            'protection_seconds': check_result['ad_settings'].get('ad_protection_seconds', 30)
        })
    
    except Exception as e:
        log_security_event('ad_display_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving ad'}), 500

@adsense_bp.route('/display/<int:display_id>/close', methods=['POST'])
def close_ad(display_id):
    """Fecha um anúncio após o período de proteção."""
    try:
        # Obter informações da requisição
        session_id = request.headers.get('X-Session-ID', 'anonymous')
        ip_address = request.remote_addr
        
        # Usar AdManager para fechar o anúncio de forma segura
        result = AdManager.close_ad_safely(display_id, session_id, ip_address)
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'ad_display': result['display']
            })
        else:
            status_code = 400
            if 'security violation' in result['error'].lower():
                status_code = 403
            elif 'not found' in result['error'].lower():
                status_code = 404
            
            response_data = {'error': result['error']}
            
            # Adicionar informações extras se disponíveis
            if 'can_close_at' in result:
                response_data['can_close_at'] = result['can_close_at']
            if 'seconds_remaining' in result:
                response_data['seconds_remaining'] = result['seconds_remaining']
            
            return jsonify(response_data), status_code
    
    except Exception as e:
        log_security_event('ad_close_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while closing ad'}), 500

@adsense_bp.route('/display/<int:display_id>/click', methods=['POST'])
def click_ad(display_id):
    """Registra um clique em um anúncio."""
    try:
        # Obter informações da requisição
        session_id = request.headers.get('X-Session-ID', 'anonymous')
        ip_address = request.remote_addr
        
        # Usar AdManager para registrar o clique de forma segura
        result = AdManager.click_ad_safely(display_id, session_id, ip_address)
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'ad_display': result['display']
            })
        else:
            status_code = 400
            if 'security violation' in result['error'].lower():
                status_code = 403
            elif 'not found' in result['error'].lower():
                status_code = 404
            
            return jsonify({'error': result['error']}), status_code
    
    except Exception as e:
        log_security_event('ad_click_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while registering ad click'}), 500

@adsense_bp.route('/analytics', methods=['GET'])
@token_required
def get_ad_analytics():
    """Obtém análises de desempenho dos anúncios."""
    try:
        # Parâmetros de data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).date()
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if not end_date:
            end_date = datetime.utcnow().date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Consultar exibições de anúncios no período
        displays = AdDisplay.query.filter(
            AdDisplay.displayed_at >= start_date,
            AdDisplay.displayed_at <= end_date + timedelta(days=1)
        ).all()
        
        # Calcular métricas
        total_displays = len(displays)
        total_clicks = sum(1 for d in displays if d.was_clicked)
        total_closed = sum(1 for d in displays if d.status == 'closed')
        
        ctr = (total_clicks / total_displays * 100) if total_displays > 0 else 0
        close_rate = (total_closed / total_displays * 100) if total_displays > 0 else 0
        
        # Métricas por placement
        placement_stats = {}
        for display in displays:
            placement = display.ad_unit.placement
            if placement not in placement_stats:
                placement_stats[placement] = {
                    'displays': 0,
                    'clicks': 0,
                    'closed': 0
                }
            
            placement_stats[placement]['displays'] += 1
            if display.was_clicked:
                placement_stats[placement]['clicks'] += 1
            if display.status == 'closed':
                placement_stats[placement]['closed'] += 1
        
        # Calcular CTR por placement
        for placement, stats in placement_stats.items():
            stats['ctr'] = (stats['clicks'] / stats['displays'] * 100) if stats['displays'] > 0 else 0
            stats['close_rate'] = (stats['closed'] / stats['displays'] * 100) if stats['displays'] > 0 else 0
        
        return jsonify({
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': {
                'total_displays': total_displays,
                'total_clicks': total_clicks,
                'total_closed': total_closed,
                'ctr': round(ctr, 2),
                'close_rate': round(close_rate, 2)
            },
            'by_placement': placement_stats
        })
    
    except Exception as e:
        log_security_event('ad_analytics_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving ad analytics'}), 500

