from flask import Blueprint, request, jsonify
from datetime import datetime
from models.user import db
from models.scenario import Scenario, Monster, ScenarioReward, PlayerScenarioProgress, ScenarioType, MonsterType
from models.player import Player
from models.item import CollectibleCard, Item
from utils.security import token_required, log_security_event
from utils.fraud_detection import FraudDetector

scenario_bp = Blueprint('scenario', __name__)

@scenario_bp.route('/list', methods=['GET'])
def list_scenarios():
    """Lista todos os cenários disponíveis."""
    try:
        # Parâmetros de filtro
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        country = request.args.get('country')
        scenario_type = request.args.get('type')
        
        # Construir query
        query = Scenario.query.filter_by(is_active=True)
        
        if country:
            query = query.filter(Scenario.country.ilike(f'%{country}%'))
        
        if scenario_type:
            try:
                scenario_type_enum = ScenarioType(scenario_type)
                query = query.filter_by(scenario_type=scenario_type_enum)
            except ValueError:
                return jsonify({'error': 'Invalid scenario type'}), 400
        
        # Ordenar por fase
        query = query.order_by(Scenario.phase_number)
        
        # Paginar
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        scenarios = pagination.items
        
        return jsonify({
            'scenarios': [scenario.to_dict() for scenario in scenarios],
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
        log_security_event('list_scenarios_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving scenarios'}), 500

@scenario_bp.route('/<int:scenario_id>', methods=['GET'])
def get_scenario(scenario_id):
    """Obtém detalhes de um cenário específico."""
    try:
        scenario = Scenario.query.get(scenario_id)
        
        if not scenario:
            return jsonify({'error': 'Scenario not found'}), 404
        
        # Buscar monstros do cenário
        monsters = Monster.query.filter_by(scenario_id=scenario_id, is_active=True).all()
        
        # Buscar recompensas do cenário
        rewards = ScenarioReward.query.filter_by(scenario_id=scenario_id, is_active=True).all()
        
        # Buscar cartas colecionáveis disponíveis nesta fase
        collectible_cards = CollectibleCard.query.filter_by(
            available_in_phase=scenario.phase_number,
            is_active=True
        ).all()
        
        # Buscar itens especiais disponíveis nesta fase
        special_items = Item.query.filter_by(
            required_phase=scenario.phase_number,
            is_active=True
        ).all()
        
        scenario_data = scenario.to_dict()
        scenario_data.update({
            'monsters': [monster.to_dict() for monster in monsters],
            'rewards': [reward.to_dict() for reward in rewards],
            'collectible_cards': [card.to_dict() for card in collectible_cards],
            'special_items': [item.to_dict() for item in special_items]
        })
        
        return jsonify(scenario_data)
    
    except Exception as e:
        log_security_event('get_scenario_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving scenario'}), 500

@scenario_bp.route('/<int:scenario_id>/monsters', methods=['GET'])
def get_scenario_monsters(scenario_id):
    """Obtém todos os monstros de um cenário."""
    try:
        scenario = Scenario.query.get(scenario_id)
        
        if not scenario:
            return jsonify({'error': 'Scenario not found'}), 404
        
        # Parâmetros de filtro
        monster_type = request.args.get('type')
        
        query = Monster.query.filter_by(scenario_id=scenario_id, is_active=True)
        
        if monster_type:
            try:
                monster_type_enum = MonsterType(monster_type)
                query = query.filter_by(monster_type=monster_type_enum)
            except ValueError:
                return jsonify({'error': 'Invalid monster type'}), 400
        
        monsters = query.all()
        
        return jsonify({
            'scenario': scenario.to_dict(),
            'monsters': [monster.to_dict() for monster in monsters],
            'total_monsters': len(monsters)
        })
    
    except Exception as e:
        log_security_event('get_scenario_monsters_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving monsters'}), 500

@scenario_bp.route('/<int:scenario_id>/progress', methods=['GET'])
@token_required
def get_scenario_progress(scenario_id):
    """Obtém o progresso do jogador em um cenário específico."""
    try:
        # Obter o ID do jogador do token
        user_id = request.token_payload.get('user_id')
        
        # Buscar o jogador
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Buscar o cenário
        scenario = Scenario.query.get(scenario_id)
        if not scenario:
            return jsonify({'error': 'Scenario not found'}), 404
        
        # Buscar ou criar progresso do cenário
        progress = PlayerScenarioProgress.query.filter_by(
            player_id=player.id,
            scenario_id=scenario_id
        ).first()
        
        if not progress:
            # Criar novo progresso se o jogador pode acessar este cenário
            if scenario.phase_number <= player.current_phase:
                progress = PlayerScenarioProgress(
                    player_id=player.id,
                    scenario_id=scenario_id,
                    total_monsters_required=scenario.calculate_total_monsters()
                )
                db.session.add(progress)
                db.session.commit()
            else:
                return jsonify({'error': 'Scenario not accessible at current phase'}), 403
        
        return jsonify({
            'scenario': scenario.to_dict(),
            'progress': progress.to_dict()
        })
    
    except Exception as e:
        log_security_event('get_scenario_progress_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving scenario progress'}), 500

@scenario_bp.route('/<int:scenario_id>/start', methods=['POST'])
@token_required
def start_scenario(scenario_id):
    """Inicia um cenário para o jogador."""
    try:
        # Obter o ID do jogador do token
        user_id = request.token_payload.get('user_id')
        
        # Buscar o jogador
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Buscar o cenário
        scenario = Scenario.query.get(scenario_id)
        if not scenario:
            return jsonify({'error': 'Scenario not found'}), 404
        
        # Verificar se o jogador pode acessar este cenário
        if scenario.phase_number > player.current_phase:
            return jsonify({'error': 'Scenario not accessible at current phase'}), 403
        
        # Verificar se já existe progresso
        existing_progress = PlayerScenarioProgress.query.filter_by(
            player_id=player.id,
            scenario_id=scenario_id
        ).first()
        
        if existing_progress and existing_progress.is_completed:
            return jsonify({'error': 'Scenario already completed'}), 400
        
        if existing_progress:
            # Resetar progresso existente se solicitado
            reset = request.get_json().get('reset', False) if request.get_json() else False
            if reset:
                existing_progress.monsters_defeated = 0
                existing_progress.deaths_in_scenario = 0
                existing_progress.items_found = 0
                existing_progress.cards_found = 0
                existing_progress.is_completed = False
                existing_progress.is_perfect = False
                existing_progress.completion_time = None
                existing_progress.started_at = datetime.utcnow()
                existing_progress.updated_at = datetime.utcnow()
        else:
            # Criar novo progresso
            existing_progress = PlayerScenarioProgress(
                player_id=player.id,
                scenario_id=scenario_id,
                total_monsters_required=scenario.calculate_total_monsters()
            )
            db.session.add(existing_progress)
        
        # Registrar para detecção de fraudes
        FraudDetector.record_player_action(player.id, 'start_scenario', {
            'scenario_id': scenario_id,
            'phase_number': scenario.phase_number
        })
        
        db.session.commit()
        
        log_security_event('scenario_started', 
                          f'Player {player.id} started scenario {scenario_id}', 
                          'info',
                          user_id=user_id)
        
        return jsonify({
            'message': 'Scenario started successfully',
            'scenario': scenario.to_dict(),
            'progress': existing_progress.to_dict()
        })
    
    except Exception as e:
        log_security_event('start_scenario_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while starting scenario'}), 500

@scenario_bp.route('/countries', methods=['GET'])
def get_countries():
    """Lista todos os países disponíveis nos cenários."""
    try:
        countries = db.session.query(Scenario.country).distinct().all()
        countries_list = [country[0] for country in countries]
        
        # Contar cenários por país
        countries_data = []
        for country in countries_list:
            scenario_count = Scenario.query.filter_by(country=country, is_active=True).count()
            countries_data.append({
                'name': country,
                'scenario_count': scenario_count
            })
        
        return jsonify({
            'countries': countries_data,
            'total_countries': len(countries_data)
        })
    
    except Exception as e:
        log_security_event('get_countries_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving countries'}), 500

@scenario_bp.route('/types', methods=['GET'])
def get_scenario_types():
    """Lista todos os tipos de cenários disponíveis."""
    try:
        types_data = []
        for scenario_type in ScenarioType:
            count = Scenario.query.filter_by(scenario_type=scenario_type, is_active=True).count()
            types_data.append({
                'type': scenario_type.value,
                'display_name': scenario_type.value.title(),
                'count': count
            })
        
        return jsonify({
            'scenario_types': types_data,
            'total_types': len(types_data)
        })
    
    except Exception as e:
        log_security_event('get_scenario_types_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving scenario types'}), 500

@scenario_bp.route('/monster-types', methods=['GET'])
def get_monster_types():
    """Lista todos os tipos de monstros disponíveis."""
    try:
        types_data = []
        for monster_type in MonsterType:
            count = Monster.query.filter_by(monster_type=monster_type, is_active=True).count()
            
            # Nome em português
            display_names = {
                MonsterType.ZOMBIE: 'Zumbi',
                MonsterType.ANIMAL: 'Animal',
                MonsterType.ROBOT: 'Robô',
                MonsterType.MUTANT: 'Mutante',
                MonsterType.ELEMENTAL: 'Elemental'
            }
            
            types_data.append({
                'type': monster_type.value,
                'display_name': display_names.get(monster_type, monster_type.value.title()),
                'count': count
            })
        
        return jsonify({
            'monster_types': types_data,
            'total_types': len(types_data)
        })
    
    except Exception as e:
        log_security_event('get_monster_types_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving monster types'}), 500

@scenario_bp.route('/player-progress', methods=['GET'])
@token_required
def get_player_all_progress():
    """Obtém o progresso do jogador em todos os cenários."""
    try:
        # Obter o ID do jogador do token
        user_id = request.token_payload.get('user_id')
        
        # Buscar o jogador
        player = Player.query.filter_by(user_id=user_id).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Buscar todo o progresso do jogador
        all_progress = PlayerScenarioProgress.query.filter_by(player_id=player.id).all()
        
        # Organizar por status
        completed_scenarios = [p for p in all_progress if p.is_completed]
        in_progress_scenarios = [p for p in all_progress if not p.is_completed]
        
        # Calcular estatísticas
        total_monsters_defeated = sum(p.monsters_defeated for p in all_progress)
        total_deaths = sum(p.deaths_in_scenario for p in all_progress)
        perfect_completions = len([p for p in completed_scenarios if p.is_perfect])
        
        return jsonify({
            'current_phase': player.current_phase,
            'completed_scenarios': [p.to_dict() for p in completed_scenarios],
            'in_progress_scenarios': [p.to_dict() for p in in_progress_scenarios],
            'statistics': {
                'total_scenarios_completed': len(completed_scenarios),
                'total_scenarios_in_progress': len(in_progress_scenarios),
                'total_monsters_defeated': total_monsters_defeated,
                'total_deaths': total_deaths,
                'perfect_completions': perfect_completions
            }
        })
    
    except Exception as e:
        log_security_event('get_player_all_progress_error', str(e), 'error')
        return jsonify({'error': 'An error occurred while retrieving player progress'}), 500

