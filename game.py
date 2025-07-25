from flask import Blueprint, request, jsonify
from models.user import db, User
from models.player import Player

game_bp = Blueprint('game', __name__)

@game_bp.route('/player/<int:user_id>', methods=['GET'])
def get_player(user_id):
    player = Player.query.filter_by(user_id=user_id).first()
    if player:
        return jsonify({'player': player.to_dict()})
    return jsonify({'error': 'Player not found'}), 404

@game_bp.route('/player/create', methods=['POST'])
def create_player():
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    # Verificar se o usuário existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Verificar se o jogador já existe
    existing_player = Player.query.filter_by(user_id=user_id).first()
    if existing_player:
        return jsonify({'player': existing_player.to_dict()})
    
    # Criar novo jogador
    player = Player(user_id=user_id, username=user.username)
    db.session.add(player)
    db.session.commit()
    
    return jsonify({'player': player.to_dict()}), 201

@game_bp.route('/player/<int:player_id>/kill-monster', methods=['POST'])
def kill_monster(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    player.monsters_killed += 1
    
    # A cada 100 monstros, restaurar vida e poder
    if player.monsters_killed % 100 == 0:
        player.health = 100
        player.power += 10
    
    db.session.commit()
    return jsonify({'player': player.to_dict()})

@game_bp.route('/player/<int:player_id>/self-eliminate', methods=['POST'])
def self_eliminate(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    # Ganhar 0.00000000000001 DOOF por auto-eliminação
    player.dooficoin_balance += 0.00000000000001
    player.self_eliminations += 1
    
    db.session.commit()
    return jsonify({'player': player.to_dict()})

@game_bp.route('/player/<int:player_id>/die', methods=['POST'])
def player_die(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    # Perder todas as moedas da partida
    player.dooficoin_balance = 0.0
    player.health = 100  # Respawn com vida cheia
    
    db.session.commit()
    return jsonify({'player': player.to_dict()})

@game_bp.route('/player/<int:player_id>/kill-player', methods=['POST'])
def kill_player(player_id):
    data = request.get_json()
    victim_id = data.get('victim_id')
    
    if not victim_id:
        return jsonify({'error': 'Victim ID is required'}), 400
    
    killer = Player.query.get(player_id)
    victim = Player.query.get(victim_id)
    
    if not killer or not victim:
        return jsonify({'error': 'Player not found'}), 404
    
    # Ganhar 20% das moedas do adversário
    stolen_coins = victim.dooficoin_balance * 0.2
    killer.dooficoin_balance += stolen_coins
    victim.dooficoin_balance -= stolen_coins
    
    db.session.commit()
    return jsonify({
        'killer': killer.to_dict(),
        'victim': victim.to_dict()
    })

