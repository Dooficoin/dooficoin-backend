from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from decimal import Decimal
from models.user import db
from models.player import Player
from models.mining import MiningSession, MiningReward, MiningStatistics
from utils.security import token_required, rate_limit, log_security_event
from utils.fraud_detection import FraudDetector

mining_bp = Blueprint('mining', __name__)

@mining_bp.route('/start', methods=['POST'])
@token_required
@rate_limit(max_requests=5, window_seconds=60)
def start_mining():
    """Inicia uma nova sessão de mineração para o jogador."""
    try:
        # Obter o ID do jogador do token
        user_id = request.token_payload.get('user_id')
        
        # Buscar o jogador
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Verificar se o jogador já tem uma sessão de mineração ativa
        active_session = MiningSession.query.filter_by(player_id=player.id, is_active=True).first()
        if active_session:
            return jsonify({
                'error': 'Player already has an active mining session',
                'session': active_session.to_dict()
            }), 400
        
        # Criar uma nova sessão de mineração
        now = datetime.utcnow()
        new_session = MiningSession(
            player_id=player.id,
            start_time=now,
            next_reward_time=now + timedelta(seconds=600),  # 10 minutos para a primeira recompensa
            current_rate="0.00000000000000000000000000000000001"  # Taxa inicial de mineração
        )
        
        db.session.add(new_session)
        db.session.commit()
        
        # Registrar a ação para detecção de fraudes
        FraudDetector.record_player_action(player.id, 'start_mining', {
            'session_id': new_session.id
        })
        
        log_security_event('mining_session_started', 
                          f'Player {player.id} started mining session {new_session.id}', 
                          'info',
                          user_id=user_id)
        
        return jsonify({
            'message': 'Mining session started successfully',
            'session': new_session.to_dict()
        }), 201
    
    except Exception as e:
        log_security_event('mining_session_start_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while starting the mining session'}), 500

@mining_bp.route('/status', methods=['GET'])
@token_required
def get_mining_status():
    """Obtém o status da sessão de mineração atual do jogador."""
    try:
        # Obter o ID do jogador do token
        user_id = request.token_payload.get('user_id')
        
        # Buscar o jogador
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Buscar a sessão de mineração ativa
        active_session = MiningSession.query.filter_by(player_id=player.id, is_active=True).first()
        
        if not active_session:
            return jsonify({
                'mining_active': False,
                'message': 'No active mining session'
            })
        
        # Verificar se é hora de gerar uma recompensa
        reward = active_session.process_mining_reward()
        
        # Se uma recompensa foi gerada, atualizar o saldo do jogador
        if reward:
            # Converter a recompensa de string para Decimal
            reward_amount = Decimal(reward.amount)
            
            # Converter o saldo atual do jogador de string para Decimal
            current_balance = Decimal(player.wallet_balance)
            
            # Adicionar a recompensa ao saldo
            new_balance = current_balance + reward_amount
            
            # Atualizar o saldo do jogador
            player.wallet_balance = str(new_balance)
            db.session.commit()
            
            # Registrar a ação para detecção de fraudes
            FraudDetector.record_player_action(player.id, 'earn_coins', {
                'amount': reward.amount,
                'source': 'mining',
                'session_id': active_session.id
            })
            
            log_security_event('mining_reward_generated', 
                              f'Player {player.id} received mining reward: {reward.amount} DOOF', 
                              'info',
                              user_id=user_id)
        
        # Obter as estatísticas de mineração do jogador
        mining_stats = MiningStatistics.query.filter_by(player_id=player.id).first()
        
        # Se não existirem estatísticas, criar um registro
        if not mining_stats:
            mining_stats = MiningStatistics(player_id=player.id)
            db.session.add(mining_stats)
            db.session.commit()
        
        # Formatar a resposta
        response = {
            'mining_active': True,
            'session': active_session.to_dict(),
            'player_balance': player.wallet_balance,
            'mining_stats': mining_stats.to_dict(),
            'last_reward': reward.to_dict() if reward else None
        }
        
        return jsonify(response)
    
    except Exception as e:
        log_security_event('mining_status_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving mining status'}), 500

@mining_bp.route('/stop', methods=['POST'])
@token_required
def stop_mining():
    """Encerra a sessão de mineração atual do jogador."""
    try:
        # Obter o ID do jogador do token
        user_id = request.token_payload.get('user_id')
        
        # Buscar o jogador
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Buscar a sessão de mineração ativa
        active_session = MiningSession.query.filter_by(player_id=player.id, is_active=True).first()
        
        if not active_session:
            return jsonify({
                'error': 'No active mining session to stop'
            }), 400
        
        # Verificar se há uma recompensa final para processar
        reward = active_session.process_mining_reward()
        
        # Se uma recompensa foi gerada, atualizar o saldo do jogador
        if reward:
            # Converter a recompensa de string para Decimal
            reward_amount = Decimal(reward.amount)
            
            # Converter o saldo atual do jogador de string para Decimal
            current_balance = Decimal(player.wallet_balance)
            
            # Adicionar a recompensa ao saldo
            new_balance = current_balance + reward_amount
            
            # Atualizar o saldo do jogador
            player.wallet_balance = str(new_balance)
            db.session.commit()
        
        # Encerrar a sessão
        active_session.end_session()
        
        # Atualizar as estatísticas de mineração
        mining_stats = MiningStatistics.query.filter_by(player_id=player.id).first()
        
        # Se não existirem estatísticas, criar um registro
        if not mining_stats:
            mining_stats = MiningStatistics(player_id=player.id)
            db.session.add(mining_stats)
            db.session.commit()
        
        # Atualizar as estatísticas com base na sessão encerrada
        mining_stats.update_stats_from_session(active_session)
        
        # Registrar a ação para detecção de fraudes
        FraudDetector.record_player_action(player.id, 'stop_mining', {
            'session_id': active_session.id,
            'duration_seconds': int((active_session.end_time - active_session.start_time).total_seconds()),
            'total_mined': active_session.total_mined
        })
        
        log_security_event('mining_session_stopped', 
                          f'Player {player.id} stopped mining session {active_session.id}', 
                          'info',
                          user_id=user_id)
        
        return jsonify({
            'message': 'Mining session stopped successfully',
            'session': active_session.to_dict(),
            'mining_stats': mining_stats.to_dict(),
            'last_reward': reward.to_dict() if reward else None
        })
    
    except Exception as e:
        log_security_event('mining_stop_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while stopping the mining session'}), 500

@mining_bp.route('/history', methods=['GET'])
@token_required
def get_mining_history():
    """Obtém o histórico de mineração do jogador."""
    try:
        # Obter o ID do jogador do token
        user_id = request.token_payload.get('user_id')
        
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)  # Limitar a 50 por página
        
        # Buscar o jogador
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Buscar as sessões de mineração do jogador (ordenadas por data, mais recentes primeiro)
        sessions_query = MiningSession.query.filter_by(player_id=player.id).order_by(MiningSession.start_time.desc())
        
        # Paginar os resultados
        sessions_pagination = sessions_query.paginate(page=page, per_page=per_page, error_out=False)
        sessions = sessions_pagination.items
        
        # Buscar as recompensas de mineração do jogador (ordenadas por data, mais recentes primeiro)
        rewards_query = MiningReward.query.filter_by(player_id=player.id).order_by(MiningReward.timestamp.desc())
        
        # Paginar os resultados
        rewards_pagination = rewards_query.paginate(page=page, per_page=per_page, error_out=False)
        rewards = rewards_pagination.items
        
        # Buscar as estatísticas de mineração do jogador
        mining_stats = MiningStatistics.query.filter_by(player_id=player.id).first()
        
        # Se não existirem estatísticas, criar um registro
        if not mining_stats:
            mining_stats = MiningStatistics(player_id=player.id)
            db.session.add(mining_stats)
            db.session.commit()
        
        # Formatar a resposta
        response = {
            'mining_stats': mining_stats.to_dict(),
            'sessions': {
                'items': [session.to_dict() for session in sessions],
                'pagination': {
                    'total_items': sessions_pagination.total,
                    'total_pages': sessions_pagination.pages,
                    'current_page': page,
                    'per_page': per_page,
                    'has_next': sessions_pagination.has_next,
                    'has_prev': sessions_pagination.has_prev
                }
            },
            'rewards': {
                'items': [reward.to_dict() for reward in rewards],
                'pagination': {
                    'total_items': rewards_pagination.total,
                    'total_pages': rewards_pagination.pages,
                    'current_page': page,
                    'per_page': per_page,
                    'has_next': rewards_pagination.has_next,
                    'has_prev': rewards_pagination.has_prev
                }
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        log_security_event('mining_history_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving mining history'}), 500

@mining_bp.route('/leaderboard', methods=['GET'])
def get_mining_leaderboard():
    """Obtém o ranking dos jogadores com mais Dooficoin minerado."""
    try:
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)  # Limitar a 50 por página
        
        # Buscar as estatísticas de mineração ordenadas por total minerado (decrescente)
        stats_query = MiningStatistics.query.order_by(MiningStatistics.total_mined_lifetime.desc())
        
        # Paginar os resultados
        pagination = stats_query.paginate(page=page, per_page=per_page, error_out=False)
        stats = pagination.items
        
        # Formatar a resposta
        leaderboard = []
        for i, stat in enumerate(stats, start=(page - 1) * per_page + 1):
            # Buscar o jogador
            player = Player.query.get(stat.player_id)
            if player:
                leaderboard.append({
                    'rank': i,
                    'player_id': stat.player_id,
                    'player_name': player.username,
                    'total_mined': stat.total_mined_lifetime,
                    'mining_level': stat.current_mining_level,
                    'total_sessions': stat.total_sessions
                })
        
        response = {
            'leaderboard': leaderboard,
            'pagination': {
                'total_items': pagination.total,
                'total_pages': pagination.pages,
                'current_page': page,
                'per_page': per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        log_security_event('mining_leaderboard_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving mining leaderboard'}), 500

