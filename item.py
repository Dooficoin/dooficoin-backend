from datetime import datetime
import json
from database import db
from enum import Enum

class ItemRarity(Enum):
    """Enum para raridade de itens."""
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"

class ItemType(Enum):
    """Enum para tipos de itens."""
    WEAPON = "weapon"
    ARMOR = "armor"
    ACCESSORY = "accessory"
    COLLECTIBLE = "collectible"
    CONSUMABLE = "consumable"
    SPECIAL = "special"

class Item(db.Model):
    """Modelo para itens do jogo com sistema de raridade."""
    
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    item_type = db.Column(db.Enum(ItemType), nullable=False)
    rarity = db.Column(db.Enum(ItemRarity), nullable=False, default=ItemRarity.COMMON)
    
    # Preços e economia
    base_price = db.Column(db.String(50), nullable=False, default="0")  # Preço base em Dooficoin
    current_price = db.Column(db.String(50), nullable=False, default="0")  # Preço atual (pode variar)
    
    # Requisitos e disponibilidade
    required_level = db.Column(db.Integer, default=1)  # Nível mínimo para usar
    required_phase = db.Column(db.Integer, default=1)  # Fase mínima para encontrar
    is_tradeable = db.Column(db.Boolean, default=True)  # Se pode ser trocado entre jogadores
    is_sellable = db.Column(db.Boolean, default=True)  # Se pode ser vendido de volta
    
    # Atributos do item
    attributes = db.Column(db.Text, default='{}')  # JSON com atributos específicos
    
    # Configurações de drop
    drop_rate = db.Column(db.Float, default=0.1)  # Taxa de drop (0.0 a 1.0)
    max_stack = db.Column(db.Integer, default=1)  # Quantidade máxima no inventário
    
    # Metadados
    image_url = db.Column(db.String(255), nullable=True)  # URL da imagem do item
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    inventory_items = db.relationship('InventoryItem', backref='item', lazy='dynamic')
    shop_items = db.relationship('ShopItem', backref='item', lazy='dynamic')
    
    def __repr__(self):
        return f'<Item {self.name}: {self.rarity.value}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'item_type': self.item_type.value,
            'rarity': self.rarity.value,
            'base_price': self.base_price,
            'current_price': self.current_price,
            'required_level': self.required_level,
            'required_phase': self.required_phase,
            'is_tradeable': self.is_tradeable,
            'is_sellable': self.is_sellable,
            'attributes': json.loads(self.attributes) if self.attributes else {},
            'drop_rate': self.drop_rate,
            'max_stack': self.max_stack,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'rarity_color': self.get_rarity_color(),
            'rarity_display': self.get_rarity_display()
        }
    
    def get_rarity_color(self):
        """Retorna a cor associada à raridade do item."""
        colors = {
            ItemRarity.COMMON: '#9CA3AF',      # Cinza
            ItemRarity.RARE: '#3B82F6',       # Azul
            ItemRarity.EPIC: '#8B5CF6',       # Roxo
            ItemRarity.LEGENDARY: '#F59E0B',  # Dourado
            ItemRarity.MYTHIC: '#EF4444'      # Vermelho
        }
        return colors.get(self.rarity, '#9CA3AF')
    
    def get_rarity_display(self):
        """Retorna o nome da raridade em português."""
        displays = {
            ItemRarity.COMMON: 'Comum',
            ItemRarity.RARE: 'Raro',
            ItemRarity.EPIC: 'Épico',
            ItemRarity.LEGENDARY: 'Lendário',
            ItemRarity.MYTHIC: 'Mítico'
        }
        return displays.get(self.rarity, 'Comum')
    
    def get_attributes(self):
        """Retorna os atributos do item como dicionário."""
        try:
            return json.loads(self.attributes) if self.attributes else {}
        except json.JSONDecodeError:
            return {}
    
    def set_attributes(self, attributes_dict):
        """Define os atributos do item."""
        self.attributes = json.dumps(attributes_dict)
    
    def can_be_used_by_player(self, player):
        """Verifica se o item pode ser usado pelo jogador."""
        return (player.level >= self.required_level and 
                player.current_phase >= self.required_phase)


class InventoryItem(db.Model):
    """Modelo para itens no inventário dos jogadores."""
    
    __tablename__ = 'inventory_items'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    is_equipped = db.Column(db.Boolean, default=False)
    acquired_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    player = db.relationship('Player', backref='inventory_items')
    
    def __repr__(self):
        return f'<InventoryItem: Player {self.player_id} - Item {self.item_id} x{self.quantity}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'player_id': self.player_id,
            'item_id': self.item_id,
            'quantity': self.quantity,
            'is_equipped': self.is_equipped,
            'acquired_at': self.acquired_at.isoformat(),
            'item': self.item.to_dict() if self.item else None
        }


class ShopItem(db.Model):
    """Modelo para itens disponíveis na loja."""
    
    __tablename__ = 'shop_items'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    price = db.Column(db.String(50), nullable=False)  # Preço em Dooficoin
    discount_percentage = db.Column(db.Float, default=0.0)  # Desconto (0.0 a 1.0)
    is_featured = db.Column(db.Boolean, default=False)  # Item em destaque
    is_available = db.Column(db.Boolean, default=True)
    stock_quantity = db.Column(db.Integer, nullable=True)  # None = estoque ilimitado
    
    # Condições de venda
    required_level = db.Column(db.Integer, default=1)
    required_phase = db.Column(db.Integer, default=1)
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ShopItem: Item {self.item_id} - Price {self.price}>'
    
    def to_dict(self):
        final_price = self.get_final_price()
        return {
            'id': self.id,
            'item_id': self.item_id,
            'price': self.price,
            'final_price': final_price,
            'discount_percentage': self.discount_percentage,
            'is_featured': self.is_featured,
            'is_available': self.is_available,
            'stock_quantity': self.stock_quantity,
            'required_level': self.required_level,
            'required_phase': self.required_phase,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'item': self.item.to_dict() if self.item else None,
            'has_discount': self.discount_percentage > 0
        }
    
    def get_final_price(self):
        """Calcula o preço final com desconto."""
        from decimal import Decimal
        base_price = Decimal(self.price)
        if self.discount_percentage > 0:
            discount = base_price * Decimal(str(self.discount_percentage))
            return str(base_price - discount)
        return self.price
    
    def can_be_purchased_by_player(self, player):
        """Verifica se o item pode ser comprado pelo jogador."""
        return (self.is_available and 
                player.level >= self.required_level and 
                player.current_phase >= self.required_phase and
                (self.stock_quantity is None or self.stock_quantity > 0))


class CollectibleCard(db.Model):
    """Modelo para figurinhas colecionáveis."""
    
    __tablename__ = 'collectible_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    card_series = db.Column(db.String(50), nullable=False)  # Série da figurinha (país, fase, etc.)
    card_number = db.Column(db.Integer, nullable=False)  # Número na série
    rarity = db.Column(db.Enum(ItemRarity), nullable=False, default=ItemRarity.COMMON)
    
    # Disponibilidade
    available_in_phase = db.Column(db.Integer, nullable=False)  # Fase onde pode ser encontrada
    drop_rate = db.Column(db.Float, default=0.05)  # Taxa de drop
    
    # Visual
    image_url = db.Column(db.String(255), nullable=True)
    background_color = db.Column(db.String(7), default='#FFFFFF')  # Cor de fundo da carta
    
    # Metadados
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    player_cards = db.relationship('PlayerCollectibleCard', backref='card', lazy='dynamic')
    
    def __repr__(self):
        return f'<CollectibleCard {self.name}: {self.card_series} #{self.card_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'card_series': self.card_series,
            'card_number': self.card_number,
            'rarity': self.rarity.value,
            'available_in_phase': self.available_in_phase,
            'drop_rate': self.drop_rate,
            'image_url': self.image_url,
            'background_color': self.background_color,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'rarity_color': self.get_rarity_color(),
            'rarity_display': self.get_rarity_display(),
            'full_number': f"{self.card_series}-{self.card_number:03d}"
        }
    
    def get_rarity_color(self):
        """Retorna a cor associada à raridade da carta."""
        colors = {
            ItemRarity.COMMON: '#9CA3AF',
            ItemRarity.RARE: '#3B82F6',
            ItemRarity.EPIC: '#8B5CF6',
            ItemRarity.LEGENDARY: '#F59E0B',
            ItemRarity.MYTHIC: '#EF4444'
        }
        return colors.get(self.rarity, '#9CA3AF')
    
    def get_rarity_display(self):
        """Retorna o nome da raridade em português."""
        displays = {
            ItemRarity.COMMON: 'Comum',
            ItemRarity.RARE: 'Raro',
            ItemRarity.EPIC: 'Épico',
            ItemRarity.LEGENDARY: 'Lendário',
            ItemRarity.MYTHIC: 'Mítico'
        }
        return displays.get(self.rarity, 'Comum')


class PlayerCollectibleCard(db.Model):
    """Modelo para figurinhas colecionáveis dos jogadores."""
    
    __tablename__ = 'player_collectible_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('collectible_cards.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)  # Quantas cartas iguais o jogador tem
    first_acquired_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    player = db.relationship('Player', backref='collectible_cards')
    
    def __repr__(self):
        return f'<PlayerCollectibleCard: Player {self.player_id} - Card {self.card_id} x{self.quantity}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'player_id': self.player_id,
            'card_id': self.card_id,
            'quantity': self.quantity,
            'first_acquired_at': self.first_acquired_at.isoformat(),
            'card': self.card.to_dict() if self.card else None
        }


class ItemDrop(db.Model):
    """Modelo para controlar drops de itens por ação."""
    
    __tablename__ = 'item_drops'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=True)
    card_id = db.Column(db.Integer, db.ForeignKey('collectible_cards.id'), nullable=True)
    
    # Contexto do drop
    drop_source = db.Column(db.String(50), nullable=False)  # 'monster_kill', 'player_kill', 'phase_completion'
    phase_number = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    
    # Metadados
    dropped_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    player = db.relationship('Player', backref='item_drops')
    
    def __repr__(self):
        return f'<ItemDrop: Player {self.player_id} - {self.drop_source} in Phase {self.phase_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'player_id': self.player_id,
            'item_id': self.item_id,
            'card_id': self.card_id,
            'drop_source': self.drop_source,
            'phase_number': self.phase_number,
            'quantity': self.quantity,
            'dropped_at': self.dropped_at.isoformat(),
            'item': self.item.to_dict() if self.item else None,
            'card': self.card.to_dict() if self.card else None
        }

