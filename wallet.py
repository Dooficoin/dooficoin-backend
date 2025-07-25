from flask import Blueprint, request, jsonify
from models.user import db
from models.player import Player

wallet_bp = Blueprint('wallet', __name__)

@wallet_bp.route('/connect', methods=['POST'])
def connect_wallet():
    data = request.get_json()
    player_id = data.get('player_id')
    wallet_address = data.get('wallet_address')
    
    if not player_id or not wallet_address:
        return jsonify({'error': 'Player ID and wallet address are required'}), 400
    
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    # Aqui seria implementada a lógica real de conexão com a carteira
    # Por enquanto, apenas simulamos o sucesso
    
    return jsonify({
        'success': True,
        'message': 'Wallet connected successfully',
        'wallet_address': wallet_address
    })

@wallet_bp.route('/disconnect', methods=['POST'])
def disconnect_wallet():
    data = request.get_json()
    player_id = data.get('player_id')
    
    if not player_id:
        return jsonify({'error': 'Player ID is required'}), 400
    
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    # Aqui seria implementada a lógica real de desconexão da carteira
    # Por enquanto, apenas simulamos o sucesso
    
    return jsonify({
        'success': True,
        'message': 'Wallet disconnected successfully'
    })

@wallet_bp.route('/withdraw', methods=['POST'])
def withdraw():
    data = request.get_json()
    player_id = data.get('player_id')
    amount = data.get('amount')
    wallet_address = data.get('wallet_address')
    
    if not player_id or not amount or not wallet_address:
        return jsonify({'error': 'Player ID, amount, and wallet address are required'}), 400
    
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    if player.dooficoin_balance < amount:
        return jsonify({'error': 'Insufficient balance'}), 400
    
    # Aqui seria implementada a lógica real de transferência para a blockchain
    # Por enquanto, apenas simulamos o sucesso
    player.dooficoin_balance -= amount
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Successfully withdrawn {amount} DOOF to {wallet_address}',
        'new_balance': player.dooficoin_balance
    })

@wallet_bp.route('/deposit', methods=['POST'])
def deposit():
    data = request.get_json()
    player_id = data.get('player_id')
    amount = data.get('amount')
    transaction_hash = data.get('transaction_hash')
    
    if not player_id or not amount or not transaction_hash:
        return jsonify({'error': 'Player ID, amount, and transaction hash are required'}), 400
    
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    # Aqui seria implementada a lógica real de verificação da transação na blockchain
    # Por enquanto, apenas simulamos o sucesso
    player.dooficoin_balance += amount
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Successfully deposited {amount} DOOF',
        'new_balance': player.dooficoin_balance
    })

@wallet_bp.route('/mine', methods=['POST'])
def mine():
    data = request.get_json()
    player_id = data.get('player_id')
    
    if not player_id:
        return jsonify({'error': 'Player ID is required'}), 400
    
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    # Simulação de mineração - ganhar uma pequena quantidade de DOOF
    mining_reward = 0.0000001
    player.dooficoin_balance += mining_reward
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Successfully mined {mining_reward} DOOF',
        'new_balance': player.dooficoin_balance
    })

