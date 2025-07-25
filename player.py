from database import db
from decimal import Decimal

class Player(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    level = db.Column(db.Integer, default=1)
    health = db.Column(db.Integer, default=100)
    power = db.Column(db.Integer, default=10)
    wallet_balance = db.Column(db.String(100), default="0")  # Saldo em string para precisão
    monsters_killed = db.Column(db.Integer, default=0)
    self_eliminations = db.Column(db.Integer, default=0)
    player_kills = db.Column(db.Integer, default=0)
    deaths = db.Column(db.Integer, default=0)
    current_phase = db.Column(db.Integer, default=1)  # Fase atual do jogador
    is_mining = db.Column(db.Boolean, default=False)
    last_activity = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    user = db.relationship('User', backref='player', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'level': self.level,
            'health': self.health,
            'power': self.power,
            'wallet_balance': self.wallet_balance,
            'monsters_killed': self.monsters_killed,
            'self_eliminations': self.self_eliminations,
            'player_kills': self.player_kills,
            'deaths': self.deaths,
            'current_phase': self.current_phase,
            'is_mining': self.is_mining,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }
    
    def add_coins(self, amount_str):
        """
        Adiciona moedas ao saldo do jogador.
        
        Args:
            amount_str: Quantidade a adicionar como string para precisão
        """
        current_balance = Decimal(self.wallet_balance)
        amount = Decimal(amount_str)
        new_balance = current_balance + amount
        self.wallet_balance = str(new_balance)
    
    def remove_coins(self, amount_str):
        """
        Remove moedas do saldo do jogador.
        
        Args:
            amount_str: Quantidade a remover como string para precisão
            
        Returns:
            bool: True se a operação foi bem-sucedida, False se o saldo for insuficiente
        """
        current_balance = Decimal(self.wallet_balance)
        amount = Decimal(amount_str)
        
        if current_balance < amount:
            return False
        
        new_balance = current_balance - amount
        self.wallet_balance = str(new_balance)
        return True
    
    def kill_monster(self):
        """
        Registra a morte de um monstro e atualiza as estatísticas do jogador.
        
        Returns:
            bool: True se o jogador atingiu um múltiplo de 100 monstros mortos
        """
        self.monsters_killed += 1
        
        # Verificar se atingiu um múltiplo de 100
        if self.monsters_killed % 100 == 0:
            # Restaurar vida e poder
            self.health = 100
            self.power += 5  # Aumentar o poder a cada 100 monstros
            
            # Aumentar o nível a cada 500 monstros
            if self.monsters_killed % 500 == 0:
                self.level += 1
            
            return True
        
        return False
    
    def self_eliminate(self):
        """
        Registra uma auto-eliminação e adiciona uma pequena quantidade de Dooficoin.
        
        Returns:
            str: Quantidade de Dooficoin ganha
        """
        self.self_eliminations += 1
        
        # Quantidade fixa de Dooficoin por auto-eliminação
        coin_reward = "0.00000000000000000000000000000000001"
        
        # Adicionar ao saldo
        self.add_coins(coin_reward)
        
        return coin_reward
    
    def die(self):
        """
        Registra a morte do jogador e zera o saldo da partida atual.
        """
        self.deaths += 1
        
        # Em um sistema real, você armazenaria o saldo da partida separadamente
        # Por enquanto, vamos simular zerando uma porcentagem do saldo total
        current_balance = Decimal(self.wallet_balance)
        loss_percentage = Decimal("0.1")  # Perder 10% do saldo total
        loss_amount = current_balance * loss_percentage
        
        if loss_amount > 0:
            self.remove_coins(str(loss_amount))
        
        # Restaurar vida
        self.health = 100
    
    def kill_player(self, target_player):
        """
        Registra a morte de outro jogador e transfere 20% das moedas dele.
        
        Args:
            target_player: O jogador alvo que foi morto
            
        Returns:
            str: Quantidade de Dooficoin ganha
        """
        self.player_kills += 1
        target_player.deaths += 1
        
        # Calcular 20% do saldo do jogador alvo
        target_balance = Decimal(target_player.wallet_balance)
        coin_reward = target_balance * Decimal("0.2")
        
        if coin_reward > 0:
            # Remover do alvo
            target_player.remove_coins(str(coin_reward))
            
            # Adicionar ao jogador
            self.add_coins(str(coin_reward))
        
        # Restaurar vida do alvo
        target_player.health = 100
        
        return str(coin_reward)

