from flask import Blueprint, request, jsonify
from datetime import datetime
from decimal import Decimal
from models.user import db
from models.player import Player
from models.level import PlayerLevel, LevelReward, PhaseProgress
from models.scenario import PlayerScenarioProgress, Scenario
from utils.security import token_required, log_security_event
from utils.fraud_detection import FraudDetector

level_bp = Blueprint('level', __name__)

@level_bp.route('/status', methods=['GET'])
@token_required
def get_level_status():
    """Obtém o status de nível e progressão do jogador."""
    try:
        # Obter o ID do jogador do token
        user_id = request.token_payload.get('user_id')
        
        # Buscar o jogador
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Buscar ou criar o registro de nível do jogador
        player_level = PlayerLevel.query.filter_by(player_id=player.id).first()
        if not player_level:
            player_level = PlayerLevel(
                player_id=player.id,
                current_level=player.level,
                current_phase=player.current_phase
            )
            db.session.add(player_level)
            db.session.commit()
        
        # Buscar recompensas não reivindicadas
        unclaimed_rewards = LevelReward.query.filter_by(
            player_level_id=player_level.id,
            is_claimed=False
        ).all()
        
        return jsonify({
            'player_level': player_level.to_dict(),
            'unclaimed_rewards': [reward.to_dict() for reward in unclaimed_rewards],
            'unclaimed_count': len(unclaimed_rewards)
        })
    
    except Exception as e:
        log_security_event('level_status_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving level status'}), 500

@level_bp.route('/kill-monster', methods=['POST'])
@token_required
def kill_monster():
    """Registra a morte de um monstro e atualiza a progressão."""
    try:
        # Obter o ID do jogador do token
        user_id = request.token_payload.get('user_id')
        
        # Buscar o jogador
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Obter dados da requisição
        data = request.get_json() or {}
        monster_id = data.get('monster_id')
        scenario_id = data.get('scenario_id', player.current_phase)
        
        # Buscar ou criar o registro de nível do jogador
        player_level = PlayerLevel.query.filter_by(player_id=player.id).first()
        if not player_level:
            player_level = PlayerLevel(
                player_id=player.id,
                current_level=player.level,
                current_phase=player.current_phase
            )
            db.session.add(player_level)
            db.session.flush()
        
        # Registrar a morte do monstro
        player_level.add_monster_kill()
        
        # Atualizar estatísticas do jogador
        player.monsters_killed += 1
        
        # Atualizar progresso do cenário
        scenario_progress = PlayerScenarioProgress.query.filter_by(
            player_id=player.id,
            scenario_id=scenario_id
        ).first()
        
        if scenario_progress:
            scenario_progress.defeat_monster()
        
        # Registrar para detecção de fraudes
        FraudDetector.record_player_action(player.id, 'kill_monster', {
            'monster_id': monster_id,
            'scenario_id': scenario_id,
            'total_monsters_killed': player.monsters_killed
        })
        
        # Verificar se houve mudança de nível
        level_changed = player_level.current_level > player.level
        if level_changed:
            player.level = player_level.current_level
        
        db.session.commit()
        
        log_security_event('monster_killed', 
                          f'Player {player.id} killed monster in scenario {scenario_id}', 
                          'info',
                          user_id=user_id)
        
        return jsonify({
            'message': 'Monster kill registered successfully',
            'player_level': player_level.to_dict(),
            'level_changed': level_changed,
            'new_level': player_level.current_level if level_changed else None,
            'scenario_progress': scenario_progress.to_dict() if scenario_progress else None
        })
    
    except Exception as e:
        log_security_event('kill_monster_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while registering monster kill'}), 500

@level_bp.route('/kill-player', methods=['POST'])
@token_required
def kill_player():
    """Registra a morte de outro jogador e atualiza a progressão."""
    try:
        # Obter o ID do jogador do token
        user_id = request.token_payload.get('user_id')
        
        # Buscar o jogador
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Obter dados da requisição
        data = request.get_json() or {}
        target_player_id = data.get('target_player_id')
        
        if not target_player_id:
            return jsonify({'error': 'Target player ID is required'}), 400
        
        # Buscar o jogador alvo
        target_player = Player.query.get(target_player_id)
        if not target_player:
            return jsonify({'error': 'Target player not found'}), 404
        
        # Buscar ou criar o registro de nível do jogador
        player_level = PlayerLevel.query.filter_by(player_id=player.id).first()
        if not player_level:
            player_level = PlayerLevel(
                player_id=player.id,
                current_level=player.level,
                current_phase=player.current_phase
            )
            db.session.add(player_level)
            db.session.flush()
        
        # Registrar a morte do jogador
        player_level.add_player_kill()
        
        # Transferir 20% das moedas do alvo
        coins_gained = player.kill_player(target_player)
        
        # Registrar para detecção de fraudes
        FraudDetector.record_player_action(player.id, 'kill_player', {
            'target_player_id': target_player_id,
            'coins_gained': coins_gained,
            'total_player_kills': player.player_kills
        })
        
        # Verificar se houve mudança de nível
        level_changed = player_level.current_level > player.level
        if level_changed:
            player.level = player_level.current_level
        
        db.session.commit()
        
        log_security_event('player_killed', 
                          f'Player {player.id} killed player {target_player_id}', 
                          'info',
                          user_id=user_id)
        
        return jsonify({
            'message': 'Player kill registered successfully',
            'coins_gained': coins_gained,
            'player_level': player_level.to_dict(),
            'level_changed': level_changed,
            'new_level': player_level.current_level if level_changed else None
        })
    
    except Exception as e:
        log_security_event('kill_player_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while registering player kill'}), 500

@level_bp.route('/claim-reward/<int:reward_id>', methods=['POST'])
@token_required
def claim_reward(reward_id):
    """Reivindica uma recompensa de nível."""
    try:
        # Obter o ID do jogador do token
        user_id = request.token_payload.get('user_id')
        
        # Buscar o jogador
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Buscar a recompensa
        reward = LevelReward.query.get(reward_id)
        if not reward:
            return jsonify({'error': 'Reward not found'}), 404
        
        # Verificar se a recompensa pertence ao jogador
        player_level = PlayerLevel.query.filter_by(player_id=player.id).first()
        if not player_level or reward.player_level_id != player_level.id:
            return jsonify({'error': 'Reward does not belong to this player'}), 403
        
        # Verificar se a recompensa já foi reivindicada
        if reward.is_claimed:
            return jsonify({'error': 'Reward already claimed'}), 400
        
        # Reivindicar a recompensa
        success = reward.claim_reward(player)
        
        if not success:
            return jsonify({'error': 'Failed to claim reward'}), 500
        
        # Registrar para detecção de fraudes
        FraudDetector.record_player_action(player.id, 'claim_reward', {
            'reward_id': reward_id,
            'reward_type': reward.reward_type,
            'level_achieved': reward.level_achieved,
            'dooficoin_amount': reward.dooficoin_reward
        })
        
        log_security_event('reward_claimed', 
                          f'Player {player.id} claimed reward {reward_id}', 
                          'info',
                          user_id=user_id)
        
        return jsonify({
            'message': 'Reward claimed successfully',
            'reward': reward.to_dict(),
            'new_balance': player.wallet_balance
        })
    
    except Exception as e:
        log_security_event('claim_reward_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while claiming reward'}), 500

@level_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Obtém o ranking dos jogadores por nível."""
    try:
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        
        # Tipo de ranking
        ranking_type = request.args.get('type', 'level')  # level, monsters, players
        
        if ranking_type == 'level':
            # Ranking por nível e experiência
            query = PlayerLevel.query.join(Player).order_by(
                PlayerLevel.current_level.desc(),
                PlayerLevel.experience_points.desc()
            )
        elif ranking_type == 'monsters':
            # Ranking por monstros mortos
            query = PlayerLevel.query.join(Player).order_by(
                PlayerLevel.total_monsters_killed.desc()
            )
        elif ranking_type == 'players':
            # Ranking por jogadores mortos
            query = PlayerLevel.query.join(Player).order_by(
                PlayerLevel.total_players_killed.desc()
            )
        else:
            return jsonify({'error': 'Invalid ranking type'}), 400
        
        # Paginar os resultados
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        player_levels = pagination.items
        
        # Formatar o leaderboard
        leaderboard = []
        for i, player_level in enumerate(player_levels, start=(page - 1) * per_page + 1):
            player_data = {
                'rank': i,
                'player_id': player_level.player_id,
                'player_name': player_level.player.username,
                'current_level': player_level.current_level,
                'current_phase': player_level.current_phase,
                'experience_points': player_level.experience_points,
                'total_monsters_killed': player_level.total_monsters_killed,
                'total_players_killed': player_level.total_players_killed,
                'last_level_up': player_level.last_level_up.isoformat() if player_level.last_level_up else None
            }
            
            # Adicionar estatística específica baseada no tipo de ranking
            if ranking_type == 'level':
                player_data['primary_stat'] = player_level.current_level
                player_data['secondary_stat'] = player_level.experience_points
            elif ranking_type == 'monsters':
                player_data['primary_stat'] = player_level.total_monsters_killed
                player_data['secondary_stat'] = player_level.current_level
            elif ranking_type == 'players':
                player_data['primary_stat'] = player_level.total_players_killed
                player_data['secondary_stat'] = player_level.current_level
            
            leaderboard.append(player_data)
        
        return jsonify({
            'leaderboard': leaderboard,
            'ranking_type': ranking_type,
            'pagination': {
                'total_items': pagination.total,
                'total_pages': pagination.pages,
                'current_page': page,
                'per_page': per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    
    except Exception as e:
        log_security_event('leaderboard_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving leaderboard'}), 500

@level_bp.route('/phase-progress', methods=['GET'])
@token_required
def get_phase_progress():
    """Obtém o progresso do jogador nas fases."""
    try:
        # Obter o ID do jogador do token
        user_id = request.token_payload.get('user_id')
        
        # Buscar o jogador
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Buscar progresso em todas as fases
        phase_progress = PhaseProgress.query.filter_by(player_id=player.id).all()
        
        # Buscar progresso em cenários específicos
        scenario_progress = PlayerScenarioProgress.query.filter_by(player_id=player.id).all()
        
        return jsonify({
            'current_phase': player.current_phase,
            'phase_progress': [progress.to_dict() for progress in phase_progress],
            'scenario_progress': [progress.to_dict() for progress in scenario_progress],
            'total_phases_completed': len([p for p in phase_progress if p.is_completed]),
            'total_scenarios_completed': len([s for s in scenario_progress if s.is_completed])
        })
    
    except Exception as e:
        log_security_event('phase_progress_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving phase progress'}), 500

@level_bp.route('/advance-phase', methods=['POST'])
@token_required
def advance_phase():
    """Avança o jogador para a próxima fase."""
    try:
        # Obter o ID do jogador do token
        user_id = request.token_payload.get('user_id')
        
        # Buscar o jogador
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Obter dados da requisição
        data = request.get_json() or {}
        target_phase = data.get('target_phase', player.current_phase + 1)
        
        # Verificar se o jogador pode avançar para a fase alvo
        if target_phase <= player.current_phase:
            return jsonify({'error': 'Cannot advance to a previous or current phase'}), 400
        
        # Verificar se o jogador completou a fase atual
        current_scenario = Scenario.query.filter_by(phase_number=player.current_phase).first()
        if current_scenario:
            scenario_progress = PlayerScenarioProgress.query.filter_by(
                player_id=player.id,
                scenario_id=current_scenario.id
            ).first()
            
            if not scenario_progress or not scenario_progress.is_completed:
                return jsonify({'error': 'Current phase must be completed before advancing'}), 400
        
        # Atualizar a fase atual do jogador
        old_phase = player.current_phase
        player.current_phase = target_phase
        
        # Atualizar o registro de nível
        player_level = PlayerLevel.query.filter_by(player_id=player.id).first()
        if player_level:
            player_level.current_phase = target_phase
        
        # Criar progresso para a nova fase se necessário
        new_scenario = Scenario.query.filter_by(phase_number=target_phase).first()
        if new_scenario:
            existing_progress = PlayerScenarioProgress.query.filter_by(
                player_id=player.id,
                scenario_id=new_scenario.id
            ).first()
            
            if not existing_progress:
                new_progress = PlayerScenarioProgress(
                    player_id=player.id,
                    scenario_id=new_scenario.id,
                    total_monsters_required=new_scenario.calculate_total_monsters()
                )
                db.session.add(new_progress)
        
        # Registrar para detecção de fraudes
        FraudDetector.record_player_action(player.id, 'advance_phase', {
            'old_phase': old_phase,
            'new_phase': target_phase
        })
        
        db.session.commit()
        
        log_security_event('phase_advanced', 
                          f'Player {player.id} advanced from phase {old_phase} to {target_phase}', 
                          'info',
                          user_id=user_id)
        
        return jsonify({
            'message': 'Phase advanced successfully',
            'old_phase': old_phase,
            'new_phase': target_phase,
            'scenario': new_scenario.to_dict() if new_scenario else None
        })
    
    except Exception as e:
        log_security_event('advance_phase_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while advancing phase'}), 500

