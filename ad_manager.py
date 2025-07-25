from datetime import datetime, timedelta
import json
from models.user import db
from models.adsense import AdSenseConfig, AdUnit, AdDisplay
from models.player import Player
from utils.security import log_security_event
from utils.fraud_detection import FraudDetector

class AdManager:
    """Gerenciador de anúncios com controle de intervalos e proteção."""
    
    @staticmethod
    def can_show_ad(placement, session_id, ip_address, player_id=None):
        """
        Verifica se um anúncio pode ser exibido para o usuário.
        
        Args:
            placement (str): Local onde o anúncio será exibido (login, mining)
            session_id (str): ID da sessão do usuário
            ip_address (str): IP do usuário
            player_id (int, optional): ID do jogador se estiver logado
        
        Returns:
            dict: Resultado da verificação com informações sobre disponibilidade
        """
        try:
            # Verificar se o AdSense está configurado e ativo
            config = AdSenseConfig.query.filter_by(is_active=True).first()
            
            if not config:
                return {
                    'can_show': False,
                    'reason': 'AdSense not configured',
                    'retry_after': None
                }
            
            # Verificar configurações de anúncios
            ad_settings = json.loads(config.ad_settings) if config.ad_settings else {}
            
            # Verificar se anúncios estão habilitados para este local
            if placement == 'login' and not ad_settings.get('login_ads_enabled', True):
                return {
                    'can_show': False,
                    'reason': 'Login ads disabled',
                    'retry_after': None
                }
            
            if placement == 'mining' and not ad_settings.get('mining_ads_enabled', True):
                return {
                    'can_show': False,
                    'reason': 'Mining ads disabled',
                    'retry_after': None
                }
            
            # Buscar uma unidade de anúncio ativa para o local
            ad_unit = AdUnit.query.filter_by(
                adsense_config_id=config.id,
                placement=placement,
                is_active=True
            ).first()
            
            if not ad_unit:
                return {
                    'can_show': False,
                    'reason': 'No ad unit configured for this placement',
                    'retry_after': None
                }
            
            # Verificar intervalo de anúncios
            ad_interval_minutes = ad_settings.get('ad_interval_minutes', 10)
            interval_check = AdManager._check_ad_interval(
                session_id, ip_address, player_id, ad_unit.id, ad_interval_minutes
            )
            
            if not interval_check['can_show']:
                return interval_check
            
            # Verificar limites de fraude
            fraud_check = AdManager._check_fraud_limits(session_id, ip_address, player_id)
            
            if not fraud_check['can_show']:
                return fraud_check
            
            return {
                'can_show': True,
                'ad_unit': ad_unit,
                'config': config,
                'ad_settings': ad_settings
            }
        
        except Exception as e:
            log_security_event('ad_manager_error', str(e), 'error')
            return {
                'can_show': False,
                'reason': 'Internal error',
                'retry_after': None
            }
    
    @staticmethod
    def _check_ad_interval(session_id, ip_address, player_id, ad_unit_id, interval_minutes):
        """Verifica se o intervalo entre anúncios foi respeitado."""
        try:
            # Verificar por sessão (mais específico)
            recent_display_session = AdDisplay.query.filter_by(
                session_id=session_id,
                ad_unit_id=ad_unit_id
            ).filter(
                AdDisplay.displayed_at > datetime.utcnow() - timedelta(minutes=interval_minutes)
            ).first()
            
            if recent_display_session:
                next_available = recent_display_session.displayed_at + timedelta(minutes=interval_minutes)
                return {
                    'can_show': False,
                    'reason': 'Ad interval not reached (session)',
                    'retry_after': next_available.isoformat(),
                    'seconds_remaining': int((next_available - datetime.utcnow()).total_seconds())
                }
            
            # Verificar por IP (proteção adicional)
            recent_display_ip = AdDisplay.query.filter_by(
                ip_address=ip_address,
                ad_unit_id=ad_unit_id
            ).filter(
                AdDisplay.displayed_at > datetime.utcnow() - timedelta(minutes=interval_minutes)
            ).first()
            
            if recent_display_ip:
                next_available = recent_display_ip.displayed_at + timedelta(minutes=interval_minutes)
                return {
                    'can_show': False,
                    'reason': 'Ad interval not reached (IP)',
                    'retry_after': next_available.isoformat(),
                    'seconds_remaining': int((next_available - datetime.utcnow()).total_seconds())
                }
            
            # Verificar por jogador se estiver logado
            if player_id:
                recent_display_player = AdDisplay.query.filter_by(
                    player_id=player_id,
                    ad_unit_id=ad_unit_id
                ).filter(
                    AdDisplay.displayed_at > datetime.utcnow() - timedelta(minutes=interval_minutes)
                ).first()
                
                if recent_display_player:
                    next_available = recent_display_player.displayed_at + timedelta(minutes=interval_minutes)
                    return {
                        'can_show': False,
                        'reason': 'Ad interval not reached (player)',
                        'retry_after': next_available.isoformat(),
                        'seconds_remaining': int((next_available - datetime.utcnow()).total_seconds())
                    }
            
            return {'can_show': True}
        
        except Exception as e:
            log_security_event('ad_interval_check_error', str(e), 'error')
            return {
                'can_show': False,
                'reason': 'Error checking ad interval',
                'retry_after': None
            }
    
    @staticmethod
    def _check_fraud_limits(session_id, ip_address, player_id):
        """Verifica limites de fraude para anúncios."""
        try:
            now = datetime.utcnow()
            
            # Limite de anúncios por IP por hora (máximo 20)
            ip_displays_hour = AdDisplay.query.filter_by(
                ip_address=ip_address
            ).filter(
                AdDisplay.displayed_at > now - timedelta(hours=1)
            ).count()
            
            if ip_displays_hour >= 20:
                return {
                    'can_show': False,
                    'reason': 'IP hourly limit exceeded',
                    'retry_after': (now + timedelta(hours=1)).isoformat()
                }
            
            # Limite de anúncios por sessão por dia (máximo 50)
            session_displays_day = AdDisplay.query.filter_by(
                session_id=session_id
            ).filter(
                AdDisplay.displayed_at > now - timedelta(days=1)
            ).count()
            
            if session_displays_day >= 50:
                return {
                    'can_show': False,
                    'reason': 'Session daily limit exceeded',
                    'retry_after': (now + timedelta(days=1)).isoformat()
                }
            
            # Se for um jogador logado, verificar limites específicos
            if player_id:
                # Limite de anúncios por jogador por dia (máximo 100)
                player_displays_day = AdDisplay.query.filter_by(
                    player_id=player_id
                ).filter(
                    AdDisplay.displayed_at > now - timedelta(days=1)
                ).count()
                
                if player_displays_day >= 100:
                    return {
                        'can_show': False,
                        'reason': 'Player daily limit exceeded',
                        'retry_after': (now + timedelta(days=1)).isoformat()
                    }
                
                # Verificar se o jogador não está sendo suspeito de fraude
                fraud_score = FraudDetector.calculate_fraud_score(player_id)
                if fraud_score > 80:  # Score alto indica possível fraude
                    return {
                        'can_show': False,
                        'reason': 'High fraud score detected',
                        'retry_after': None
                    }
            
            return {'can_show': True}
        
        except Exception as e:
            log_security_event('ad_fraud_check_error', str(e), 'error')
            return {
                'can_show': False,
                'reason': 'Error checking fraud limits',
                'retry_after': None
            }
    
    @staticmethod
    def create_ad_display(ad_unit, session_id, ip_address, user_agent, player_id=None):
        """
        Cria um registro de exibição de anúncio.
        
        Args:
            ad_unit (AdUnit): Unidade de anúncio a ser exibida
            session_id (str): ID da sessão do usuário
            ip_address (str): IP do usuário
            user_agent (str): User agent do navegador
            player_id (int, optional): ID do jogador se estiver logado
        
        Returns:
            AdDisplay: Registro de exibição criado
        """
        try:
            # Obter configurações de proteção
            config = AdSenseConfig.query.filter_by(is_active=True).first()
            ad_settings = json.loads(config.ad_settings) if config and config.ad_settings else {}
            protection_seconds = ad_settings.get('ad_protection_seconds', 30)
            
            # Criar registro de exibição
            ad_display = AdDisplay(
                ad_unit_id=ad_unit.id,
                player_id=player_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                protection_end_time=datetime.utcnow() + timedelta(seconds=protection_seconds)
            )
            
            db.session.add(ad_display)
            db.session.commit()
            
            # Registrar para detecção de fraudes
            if player_id:
                FraudDetector.record_player_action(player_id, 'view_ad', {
                    'ad_unit_id': ad_unit.id,
                    'placement': ad_unit.placement,
                    'display_id': ad_display.id,
                    'protection_seconds': protection_seconds
                })
            
            log_security_event('ad_display_created', 
                              f'Ad display created: Unit {ad_unit.id} at {ad_unit.placement}', 
                              'info')
            
            return ad_display
        
        except Exception as e:
            log_security_event('ad_display_creation_error', str(e), 'error')
            raise
    
    @staticmethod
    def get_ad_status(display_id):
        """
        Obtém o status atual de um anúncio exibido.
        
        Args:
            display_id (int): ID do registro de exibição
        
        Returns:
            dict: Status do anúncio com informações de tempo
        """
        try:
            ad_display = AdDisplay.query.get(display_id)
            
            if not ad_display:
                return {
                    'found': False,
                    'error': 'Ad display not found'
                }
            
            now = datetime.utcnow()
            can_close = ad_display.can_be_closed()
            
            # Calcular tempo restante para poder fechar
            seconds_remaining = 0
            if not can_close:
                seconds_remaining = int((ad_display.protection_end_time - now).total_seconds())
            
            return {
                'found': True,
                'display': ad_display.to_dict(),
                'can_close': can_close,
                'seconds_remaining': max(0, seconds_remaining),
                'protection_end_time': ad_display.protection_end_time.isoformat(),
                'status': ad_display.status
            }
        
        except Exception as e:
            log_security_event('ad_status_error', str(e), 'error')
            return {
                'found': False,
                'error': 'Error retrieving ad status'
            }
    
    @staticmethod
    def close_ad_safely(display_id, session_id, ip_address):
        """
        Fecha um anúncio de forma segura, verificando permissões.
        
        Args:
            display_id (int): ID do registro de exibição
            session_id (str): ID da sessão (para verificação)
            ip_address (str): IP do usuário (para verificação)
        
        Returns:
            dict: Resultado da operação de fechamento
        """
        try:
            ad_display = AdDisplay.query.get(display_id)
            
            if not ad_display:
                return {
                    'success': False,
                    'error': 'Ad display not found'
                }
            
            # Verificar se a sessão/IP corresponde (segurança básica)
            if ad_display.session_id != session_id and ad_display.ip_address != ip_address:
                log_security_event('ad_close_security_violation', 
                                  f'Attempt to close ad {display_id} from different session/IP', 
                                  'warning')
                return {
                    'success': False,
                    'error': 'Security violation: session/IP mismatch'
                }
            
            # Verificar se o anúncio pode ser fechado
            if not ad_display.can_be_closed():
                return {
                    'success': False,
                    'error': 'Ad protection period not expired',
                    'can_close_at': ad_display.protection_end_time.isoformat(),
                    'seconds_remaining': int((ad_display.protection_end_time - datetime.utcnow()).total_seconds())
                }
            
            # Fechar o anúncio
            success = ad_display.close_ad()
            
            if success:
                # Registrar para detecção de fraudes
                if ad_display.player_id:
                    duration_seconds = int((ad_display.closed_at - ad_display.displayed_at).total_seconds())
                    FraudDetector.record_player_action(ad_display.player_id, 'close_ad', {
                        'display_id': ad_display.id,
                        'duration_seconds': duration_seconds,
                        'closed_after_protection': True
                    })
                
                log_security_event('ad_closed_safely', 
                                  f'Ad closed safely: Display {ad_display.id}', 
                                  'info')
                
                return {
                    'success': True,
                    'message': 'Ad closed successfully',
                    'display': ad_display.to_dict()
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to close ad'
                }
        
        except Exception as e:
            log_security_event('ad_close_safely_error', str(e), 'error')
            return {
                'success': False,
                'error': 'Internal error while closing ad'
            }
    
    @staticmethod
    def click_ad_safely(display_id, session_id, ip_address):
        """
        Registra um clique em anúncio de forma segura.
        
        Args:
            display_id (int): ID do registro de exibição
            session_id (str): ID da sessão (para verificação)
            ip_address (str): IP do usuário (para verificação)
        
        Returns:
            dict: Resultado da operação de clique
        """
        try:
            ad_display = AdDisplay.query.get(display_id)
            
            if not ad_display:
                return {
                    'success': False,
                    'error': 'Ad display not found'
                }
            
            # Verificar se a sessão/IP corresponde (segurança básica)
            if ad_display.session_id != session_id and ad_display.ip_address != ip_address:
                log_security_event('ad_click_security_violation', 
                                  f'Attempt to click ad {display_id} from different session/IP', 
                                  'warning')
                return {
                    'success': False,
                    'error': 'Security violation: session/IP mismatch'
                }
            
            # Verificar se o anúncio pode ser clicado
            if ad_display.status != 'displayed':
                return {
                    'success': False,
                    'error': 'Ad not available for clicking'
                }
            
            # Registrar o clique
            success = ad_display.click_ad()
            
            if success:
                # Registrar para detecção de fraudes
                if ad_display.player_id:
                    time_to_click = int((ad_display.click_timestamp - ad_display.displayed_at).total_seconds())
                    
                    # Verificar se o clique foi muito rápido (possível bot)
                    if time_to_click < 2:
                        FraudDetector.record_player_action(ad_display.player_id, 'suspicious_ad_click', {
                            'display_id': ad_display.id,
                            'time_to_click_seconds': time_to_click,
                            'reason': 'Click too fast'
                        })
                    else:
                        FraudDetector.record_player_action(ad_display.player_id, 'click_ad', {
                            'display_id': ad_display.id,
                            'time_to_click_seconds': time_to_click
                        })
                
                log_security_event('ad_clicked_safely', 
                                  f'Ad clicked safely: Display {ad_display.id}', 
                                  'info')
                
                return {
                    'success': True,
                    'message': 'Ad click registered successfully',
                    'display': ad_display.to_dict()
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to register ad click'
                }
        
        except Exception as e:
            log_security_event('ad_click_safely_error', str(e), 'error')
            return {
                'success': False,
                'error': 'Internal error while registering ad click'
            }

