from flask import Blueprint, request, jsonify
from models.user import db, User
from models.item import Item, ItemRarity, ItemType, InventoryItem, ShopItem
from models.scenario import Scenario, Monster, ScenarioReward, PlayerScenarioProgress, ScenarioType, MonsterType
from models.level import LevelReward
from models.player import Player
from models.transaction import Transaction
from models.mining import MiningSession, MiningStatistics
from models.adsense import AdSenseConfig, AdUnit, AdDisplay, AdRevenue
from models.security_log import SecurityLog
from models.auth import RevokedToken
from models.item import CollectibleCard, PlayerCollectibleCard
from utils.security import token_required, admin_required, log_security_event
from decimal import Decimal
import json

admin_bp = Blueprint("admin", __name__)

# --- Item Management ---
@admin_bp.route("/items", methods=["POST"])
@token_required
@admin_required
def create_item():
    """Cria um novo item."""
    data = request.get_json()
    try:
        new_item = Item(
            name=data["name"],
            description=data.get("description"),
            item_type=ItemType[data["item_type"].upper()],
            rarity=ItemRarity[data["rarity"].upper()],
            base_price=str(data.get("base_price", "0")),
            current_price=str(data.get("current_price", "0")),
            required_level=data.get("required_level", 1),
            required_phase=data.get("required_phase", 1),
            is_tradeable=data.get("is_tradeable", True),
            is_sellable=data.get("is_sellable", True),
            attributes=json.dumps(data.get("attributes", {})),
            drop_rate=data.get("drop_rate", 0.1),
            max_stack=data.get("max_stack", 1),
            image_url=data.get("image_url"),
            is_active=data.get("is_active", True)
        )
        db.session.add(new_item)
        db.session.commit()
        log_security_event("admin_action", f"Admin created item: {new_item.name}", "info", user_id=request.token_payload["user_id"])
        return jsonify(new_item.to_dict()), 201
    except KeyError as e:
        return jsonify({"error": f"Missing or invalid field: {e}"}), 400
    except ValueError as e:
        return jsonify({"error": f"Invalid enum value: {e}"}), 400
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error creating item: {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/items", methods=["GET"])
@token_required
@admin_required
def get_all_items():
    """Retorna todos os itens com paginação e filtros."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    name = request.args.get("name")
    item_type = request.args.get("item_type")
    rarity = request.args.get("rarity")

    query = Item.query

    if name:
        query = query.filter(Item.name.ilike(f"%{name}%"))
    if item_type:
        try:
            query = query.filter_by(item_type=ItemType[item_type.upper()])
        except KeyError:
            return jsonify({"error": "Invalid item_type"}), 400
    if rarity:
        try:
            query = query.filter_by(rarity=ItemRarity[rarity.upper()])
        except KeyError:
            return jsonify({"error": "Invalid rarity"}), 400

    items = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [item.to_dict() for item in items.items],
        "total_items": items.total,
        "total_pages": items.pages,
        "current_page": items.page
    })

@admin_bp.route("/items/<int:item_id>", methods=["GET"])
@token_required
@admin_required
def get_item(item_id):
    """Retorna um item específico pelo ID."""
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item.to_dict())

@admin_bp.route("/items/<int:item_id>", methods=["PUT"])
@token_required
@admin_required
def update_item(item_id):
    """Atualiza um item existente."""
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    data = request.get_json()
    try:
        item.name = data.get("name", item.name)
        item.description = data.get("description", item.description)
        if "item_type" in data: item.item_type = ItemType[data["item_type"].upper()]
        if "rarity" in data: item.rarity = ItemRarity[data["rarity"].upper()]
        item.base_price = str(data.get("base_price", item.base_price))
        item.current_price = str(data.get("current_price", item.current_price))
        item.required_level = data.get("required_level", item.required_level)
        item.required_phase = data.get("required_phase", item.required_phase)
        item.is_tradeable = data.get("is_tradeable", item.is_tradeable)
        item.is_sellable = data.get("is_sellable", item.is_sellable)
        item.attributes = json.dumps(data.get("attributes", item.get_attributes()))
        item.drop_rate = data.get("drop_rate", item.drop_rate)
        item.max_stack = data.get("max_stack", item.max_stack)
        item.image_url = data.get("image_url", item.image_url)
        item.is_active = data.get("is_active", item.is_active)

        db.session.commit()
        log_security_event("admin_action", f"Admin updated item: {item.name} (ID: {item.id})", "info", user_id=request.token_payload["user_id"])
        return jsonify(item.to_dict())
    except KeyError as e:
        return jsonify({"error": f"Missing or invalid field: {e}"}), 400
    except ValueError as e:
        return jsonify({"error": f"Invalid enum value: {e}"}), 400
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error updating item (ID: {item_id}): {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/items/<int:item_id>", methods=["DELETE"])
@token_required
@admin_required
def delete_item(item_id):
    """Deleta um item."""
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    try:
        # Opcional: remover itens do inventário dos jogadores ou desativá-los
        # InventoryItem.query.filter_by(item_id=item_id).delete()
        # ShopItem.query.filter_by(item_id=item_id).delete()
        db.session.delete(item)
        db.session.commit()
        log_security_event("admin_action", f"Admin deleted item: {item.name} (ID: {item.id})", "info", user_id=request.token_payload["user_id"])
        return jsonify({"message": "Item deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error deleting item (ID: {item_id}): {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

# --- Scenario Management ---
@admin_bp.route("/scenarios", methods=["POST"])
@token_required
@admin_required
def create_scenario():
    """Cria um novo cenário."""
    data = request.get_json()
    try:
        new_scenario = Scenario(
            name=data["name"],
            description=data.get("description"),
            country=data["country"],
            city=data["city"],
            location_name=data.get("location_name"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            phase_number=data.get("phase_number", 1),
            scenario_type=ScenarioType[data["scenario_type"].upper()],
            difficulty_level=data.get("difficulty_level", 1),
            initial_monsters=data.get("initial_monsters", 300),
            monster_increase_percentage=data.get("monster_increase_percentage", 0.25),
            ambient_color=data.get("ambient_color", "#000000"),
            image_url=data.get("image_url"),
            is_active=data.get("is_active", True)
        )
        db.session.add(new_scenario)
        db.session.commit()
        log_security_event("admin_action", f"Admin created scenario: {new_scenario.name}", "info", user_id=request.token_payload["user_id"])
        return jsonify(new_scenario.to_dict()), 201
    except KeyError as e:
        return jsonify({"error": f"Missing or invalid field: {e}"}), 400
    except ValueError as e:
        return jsonify({"error": f"Invalid enum value: {e}"}), 400
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error creating scenario: {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/scenarios", methods=["GET"])
@token_required
@admin_required
def get_all_scenarios():
    """Retorna todos os cenários com paginação e filtros."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    name = request.args.get("name")
    country = request.args.get("country")
    scenario_type = request.args.get("scenario_type")

    query = Scenario.query

    if name:
        query = query.filter(Scenario.name.ilike(f"%{name}%"))
    if country:
        query = query.filter(Scenario.country.ilike(f"%{country}%"))
    if scenario_type:
        try:
            query = query.filter_by(scenario_type=ScenarioType[scenario_type.upper()])
        except KeyError:
            return jsonify({"error": "Invalid scenario_type"}), 400

    scenarios = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "scenarios": [s.to_dict() for s in scenarios.items],
        "total_scenarios": scenarios.total,
        "total_pages": scenarios.pages,
        "current_page": scenarios.page
    })

@admin_bp.route("/scenarios/<int:scenario_id>", methods=["GET"])
@token_required
@admin_required
def get_scenario_admin(scenario_id):
    """Retorna um cenário específico pelo ID."""
    scenario = Scenario.query.get(scenario_id)
    if not scenario:
        return jsonify({"error": "Scenario not found"}), 404
    return jsonify(scenario.to_dict())

@admin_bp.route("/scenarios/<int:scenario_id>", methods=["PUT"])
@token_required
@admin_required
def update_scenario(scenario_id):
    """Atualiza um cenário existente."""
    scenario = Scenario.query.get(scenario_id)
    if not scenario:
        return jsonify({"error": "Scenario not found"}), 404

    data = request.get_json()
    try:
        scenario.name = data.get("name", scenario.name)
        scenario.description = data.get("description", scenario.description)
        scenario.country = data.get("country", scenario.country)
        scenario.city = data.get("city", scenario.city)
        scenario.location_name = data.get("location_name", scenario.location_name)
        scenario.latitude = data.get("latitude", scenario.latitude)
        scenario.longitude = data.get("longitude", scenario.longitude)
        scenario.phase_number = data.get("phase_number", scenario.phase_number)
        if "scenario_type" in data: scenario.scenario_type = ScenarioType[data["scenario_type"].upper()]
        scenario.difficulty_level = data.get("difficulty_level", scenario.difficulty_level)
        scenario.initial_monsters = data.get("initial_monsters", scenario.initial_monsters)
        scenario.monster_increase_percentage = data.get("monster_increase_percentage", scenario.monster_increase_percentage)
        scenario.ambient_color = data.get("ambient_color", scenario.ambient_color)
        scenario.image_url = data.get("image_url", scenario.image_url)
        scenario.is_active = data.get("is_active", scenario.is_active)

        db.session.commit()
        log_security_event("admin_action", f"Admin updated scenario: {scenario.name} (ID: {scenario.id})", "info", user_id=request.token_payload["user_id"])
        return jsonify(scenario.to_dict())
    except KeyError as e:
        return jsonify({"error": f"Missing or invalid field: {e}"}), 400
    except ValueError as e:
        return jsonify({"error": f"Invalid enum value: {e}"}), 400
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error updating scenario (ID: {scenario_id}): {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/scenarios/<int:scenario_id>", methods=["DELETE"])
@token_required
@admin_required
def delete_scenario(scenario_id):
    """Deleta um cenário."""
    scenario = Scenario.query.get(scenario_id)
    if not scenario:
        return jsonify({"error": "Scenario not found"}), 404

    try:
        db.session.delete(scenario)
        db.session.commit()
        log_security_event("admin_action", f"Admin deleted scenario: {scenario.name} (ID: {scenario.id})", "info", user_id=request.token_payload["user_id"])
        return jsonify({"message": "Scenario deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error deleting scenario (ID: {scenario_id}): {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

# --- Monster Management ---
@admin_bp.route("/monsters", methods=["POST"])
@token_required
@admin_required
def create_monster():
    """Cria um novo monstro."""
    data = request.get_json()
    try:
        new_monster = Monster(
            name=data["name"],
            description=data.get("description"),
            monster_type=MonsterType[data["monster_type"].upper()],
            health=data.get("health", 100),
            attack=data.get("attack", 10),
            defense=data.get("defense", 5),
            speed=data.get("speed", 5),
            xp_reward=data.get("xp_reward", 10),
            dooficoin_reward=str(data.get("dooficoin_reward", "0.00000000000000000000000000000000001")),
            image_url=data.get("image_url"),
            is_active=data.get("is_active", True),
            scenario_id=data.get("scenario_id") # Optional, can be global monster
        )
        db.session.add(new_monster)
        db.session.commit()
        log_security_event("admin_action", f"Admin created monster: {new_monster.name}", "info", user_id=request.token_payload["user_id"])
        return jsonify(new_monster.to_dict()), 201
    except KeyError as e:
        return jsonify({"error": f"Missing or invalid field: {e}"}), 400
    except ValueError as e:
        return jsonify({"error": f"Invalid enum value: {e}"}), 400
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error creating monster: {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/monsters", methods=["GET"])
@token_required
@admin_required
def get_all_monsters():
    """Retorna todos os monstros com paginação e filtros."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    name = request.args.get("name")
    monster_type = request.args.get("monster_type")
    scenario_id = request.args.get("scenario_id", type=int)

    query = Monster.query

    if name:
        query = query.filter(Monster.name.ilike(f"%{name}%"))
    if monster_type:
        try:
            query = query.filter_by(monster_type=MonsterType[monster_type.upper()])
        except KeyError:
            return jsonify({"error": "Invalid monster_type"}), 400
    if scenario_id:
        query = query.filter_by(scenario_id=scenario_id)

    monsters = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "monsters": [m.to_dict() for m in monsters.items],
        "total_monsters": monsters.total,
        "total_pages": monsters.pages,
        "current_page": monsters.page
    })

@admin_bp.route("/monsters/<int:monster_id>", methods=["GET"])
@token_required
@admin_required
def get_monster(monster_id):
    """Retorna um monstro específico pelo ID."""
    monster = Monster.query.get(monster_id)
    if not monster:
        return jsonify({"error": "Monster not found"}), 404
    return jsonify(monster.to_dict())

@admin_bp.route("/monsters/<int:monster_id>", methods=["PUT"])
@token_required
@admin_required
def update_monster(monster_id):
    """Atualiza um monstro existente."""
    monster = Monster.query.get(monster_id)
    if not monster:
        return jsonify({"error": "Monster not found"}), 404

    data = request.get_json()
    try:
        monster.name = data.get("name", monster.name)
        monster.description = data.get("description", monster.description)
        if "monster_type" in data: monster.monster_type = MonsterType[data["monster_type"].upper()]
        monster.health = data.get("health", monster.health)
        monster.attack = data.get("attack", monster.attack)
        monster.defense = data.get("defense", monster.defense)
        monster.speed = data.get("speed", monster.speed)
        monster.xp_reward = data.get("xp_reward", monster.xp_reward)
        monster.dooficoin_reward = str(data.get("dooficoin_reward", monster.dooficoin_reward))
        monster.image_url = data.get("image_url", monster.image_url)
        monster.is_active = data.get("is_active", monster.is_active)
        monster.scenario_id = data.get("scenario_id", monster.scenario_id)

        db.session.commit()
        log_security_event("admin_action", f"Admin updated monster: {monster.name} (ID: {monster.id})", "info", user_id=request.token_payload["user_id"])
        return jsonify(monster.to_dict())
    except KeyError as e:
        return jsonify({"error": f"Missing or invalid field: {e}"}), 400
    except ValueError as e:
        return jsonify({"error": f"Invalid enum value: {e}"}), 400
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error updating monster (ID: {monster_id}): {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/monsters/<int:monster_id>", methods=["DELETE"])
@token_required
@admin_required
def delete_monster(monster_id):
    """Deleta um monstro."""
    monster = Monster.query.get(monster_id)
    if not monster:
        return jsonify({"error": "Monster not found"}), 404

    try:
        db.session.delete(monster)
        db.session.commit()
        log_security_event("admin_action", f"Admin deleted monster: {monster.name} (ID: {monster.id})", "info", user_id=request.token_payload["user_id"])
        return jsonify({"message": "Monster deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error deleting monster (ID: {monster_id}): {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

# --- Collectible Card Management ---
@admin_bp.route("/cards", methods=["POST"])
@token_required
@admin_required
def create_card():
    """Cria uma nova carta colecionável."""
    data = request.get_json()
    try:
        new_card = CollectibleCard(
            name=data["name"],
            description=data.get("description"),
            card_series=data["card_series"],
            card_number=data["card_number"],
            rarity=ItemRarity[data["rarity"].upper()],
            available_in_phase=data.get("available_in_phase", 1),
            drop_rate=data.get("drop_rate", 0.05),
            image_url=data.get("image_url"),
            background_color=data.get("background_color", "#FFFFFF"),
            is_active=data.get("is_active", True)
        )
        db.session.add(new_card)
        db.session.commit()
        log_security_event("admin_action", f"Admin created collectible card: {new_card.name}", "info", user_id=request.token_payload["user_id"])
        return jsonify(new_card.to_dict()), 201
    except KeyError as e:
        return jsonify({"error": f"Missing or invalid field: {e}"}), 400
    except ValueError as e:
        return jsonify({"error": f"Invalid enum value: {e}"}), 400
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error creating collectible card: {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/cards", methods=["GET"])
@token_required
@admin_required
def get_all_cards():
    """Retorna todas as cartas colecionáveis com paginação e filtros."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    name = request.args.get("name")
    card_series = request.args.get("card_series")
    rarity = request.args.get("rarity")

    query = CollectibleCard.query

    if name:
        query = query.filter(CollectibleCard.name.ilike(f"%{name}%"))
    if card_series:
        query = query.filter(CollectibleCard.card_series.ilike(f"%{card_series}%"))
    if rarity:
        try:
            query = query.filter_by(rarity=ItemRarity[rarity.upper()])
        except KeyError:
            return jsonify({"error": "Invalid rarity"}), 400

    cards = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "cards": [c.to_dict() for c in cards.items],
        "total_cards": cards.total,
        "total_pages": cards.pages,
        "current_page": cards.page
    })

@admin_bp.route("/cards/<int:card_id>", methods=["GET"])
@token_required
@admin_required
def get_card(card_id):
    """Retorna uma carta colecionável específica pelo ID."""
    card = CollectibleCard.query.get(card_id)
    if not card:
        return jsonify({"error": "Collectible card not found"}), 404
    return jsonify(card.to_dict())

@admin_bp.route("/cards/<int:card_id>", methods=["PUT"])
@token_required
@admin_required
def update_card(card_id):
    """Atualiza uma carta colecionável existente."""
    card = CollectibleCard.query.get(card_id)
    if not card:
        return jsonify({"error": "Collectible card not found"}), 404

    data = request.get_json()
    try:
        card.name = data.get("name", card.name)
        card.description = data.get("description", card.description)
        card.card_series = data.get("card_series", card.card_series)
        card.card_number = data.get("card_number", card.card_number)
        if "rarity" in data: card.rarity = ItemRarity[data["rarity"].upper()]
        card.available_in_phase = data.get("available_in_phase", card.available_in_phase)
        card.drop_rate = data.get("drop_rate", card.drop_rate)
        card.image_url = data.get("image_url", card.image_url)
        card.background_color = data.get("background_color", card.background_color)
        card.is_active = data.get("is_active", card.is_active)

        db.session.commit()
        log_security_event("admin_action", f"Admin updated collectible card: {card.name} (ID: {card.id})", "info", user_id=request.token_payload["user_id"])
        return jsonify(card.to_dict())
    except KeyError as e:
        return jsonify({"error": f"Missing or invalid field: {e}"}), 400
    except ValueError as e:
        return jsonify({"error": f"Invalid enum value: {e}"}), 400
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error updating collectible card (ID: {card_id}): {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/cards/<int:card_id>", methods=["DELETE"])
@token_required
@admin_required
def delete_card(card_id):
    """Deleta uma carta colecionável."""
    card = CollectibleCard.query.get(card_id)
    if not card:
        return jsonify({"error": "Collectible card not found"}), 404

    try:
        db.session.delete(card)
        db.session.commit()
        log_security_event("admin_action", f"Admin deleted collectible card: {card.name} (ID: {card.id})", "info", user_id=request.token_payload["user_id"])
        return jsonify({"message": "Collectible card deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error deleting collectible card (ID: {card_id}): {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

# --- User Management ---
@admin_bp.route("/users", methods=["GET"])
@token_required
@admin_required
def get_all_users():
    """Retorna todos os usuários com paginação e filtros."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    username = request.args.get("username")
    email = request.args.get("email")

    query = User.query

    if username:
        query = query.filter(User.username.ilike(f"%{username}%"))
    if email:
        query = query.filter(User.email.ilike(f"%{email}%"))

    users = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "users": [u.to_dict() for u in users.items],
        "total_users": users.total,
        "total_pages": users.pages,
        "current_page": users.page
    })

@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@token_required
@admin_required
def get_user(user_id):
    """Retorna um usuário específico pelo ID."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict())

@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@token_required
@admin_required
def update_user(user_id):
    """Atualiza um usuário existente."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    try:
        user.username = data.get("username", user.username)
        user.email = data.get("email", user.email)
        user.is_admin = data.get("is_admin", user.is_admin)
        user.is_active = data.get("is_active", user.is_active)
        # Adicionar lógica para resetar senha se necessário, mas com cuidado

        db.session.commit()
        log_security_event("admin_action", f"Admin updated user: {user.username} (ID: {user.id})", "info", user_id=request.token_payload["user_id"])
        return jsonify(user.to_dict())
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error updating user (ID: {user_id}): {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/users/<int:user_id>/ban", methods=["POST"])
@token_required
@admin_required
def ban_user(user_id):
    """Bane um usuário (desativa a conta)."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        user.is_active = False
        db.session.commit()
        log_security_event("admin_action", f"Admin banned user: {user.username} (ID: {user.id})", "warning", user_id=request.token_payload["user_id"])
        return jsonify({"message": f"User {user.username} banned successfully"}), 200
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error banning user (ID: {user_id}): {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/users/<int:user_id>/unban", methods=["POST"])
@token_required
@admin_required
def unban_user(user_id):
    """Desbane um usuário (ativa a conta)."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        user.is_active = True
        db.session.commit()
        log_security_event("admin_action", f"Admin unbanned user: {user.username} (ID: {user.id})", "info", user_id=request.token_payload["user_id"])
        return jsonify({"message": f"User {user.username} unbanned successfully"}), 200
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error unbanning user (ID: {user_id}): {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

# --- General Stats/Dashboard ---
@admin_bp.route("/dashboard", methods=["GET"])
@token_required
@admin_required
def get_dashboard_stats():
    """Retorna estatísticas gerais para o dashboard administrativo."""
    try:
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_items = Item.query.count()
        total_scenarios = Scenario.query.count()
        total_monsters = Monster.query.count()
        total_cards = CollectibleCard.query.count()
        total_transactions = Transaction.query.count()
        total_dooficoin_mined = db.session.query(db.func.sum(MiningStat.total_mined)).scalar() or Decimal("0")
        total_security_logs = SecurityLog.query.count()

        return jsonify({
            "total_users": total_users,
            "active_users": active_users,
            "total_items": total_items,
            "total_scenarios": total_scenarios,
            "total_monsters": total_monsters,
            "total_cards": total_cards,
            "total_transactions": total_transactions,
            "total_dooficoin_mined": str(total_dooficoin_mined),
            "total_security_logs": total_security_logs
        })
    except Exception as e:
        log_security_event("admin_dashboard_error", f"Error fetching dashboard stats: {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

# --- Security Logs ---
@admin_bp.route("/security-logs", methods=["GET"])
@token_required
@admin_required
def get_security_logs():
    """Retorna logs de segurança com paginação e filtros."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    log_type = request.args.get("type")
    user_id = request.args.get("user_id", type=int)

    query = SecurityLog.query

    if log_type:
        query = query.filter_by(log_type=log_type)
    if user_id:
        query = query.filter_by(user_id=user_id)

    logs = query.order_by(SecurityLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "logs": [log.to_dict() for log in logs.items],
        "total_logs": logs.total,
        "total_pages": logs.pages,
        "current_page": logs.page
    })

# --- AdSense Management (Admin) ---
@admin_bp.route("/adsense/config", methods=["GET"])
@token_required
@admin_required
def get_adsense_config_admin():
    """Obtém a configuração do AdSense para o admin."""
    config = AdSenseConfig.query.first()
    if not config:
        return jsonify({"error": "AdSense config not found"}), 404
    return jsonify(config.to_dict())

@admin_bp.route("/adsense/config", methods=["PUT"])
@token_required
@admin_required
def update_adsense_config_admin():
    """Atualiza a configuração do AdSense."""
    config = AdSenseConfig.query.first()
    if not config:
        config = AdSenseConfig()
        db.session.add(config)

    data = request.get_json()
    try:
        config.client_id = data.get("client_id", config.client_id)
        config.client_secret = data.get("client_secret", config.client_secret)
        config.redirect_uri = data.get("redirect_uri", config.redirect_uri)
        config.access_token = data.get("access_token", config.access_token)
        config.refresh_token = data.get("refresh_token", config.refresh_token)
        config.token_expiry = data.get("token_expiry", config.token_expiry)
        config.ad_display_interval_minutes = data.get("ad_display_interval_minutes", config.ad_display_interval_minutes)
        config.ad_display_duration_seconds = data.get("ad_display_duration_seconds", config.ad_display_duration_seconds)
        config.fraud_detection_threshold = data.get("fraud_detection_threshold", config.fraud_detection_threshold)
        config.is_active = data.get("is_active", config.is_active)

        db.session.commit()
        log_security_event("admin_action", "Admin updated AdSense config", "info", user_id=request.token_payload["user_id"])
        return jsonify(config.to_dict())
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error updating AdSense config: {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/adsense/ad-units", methods=["POST"])
@token_required
@admin_required
def create_ad_unit_admin():
    """Cria uma nova unidade de anúncio."""
    data = request.get_json()
    try:
        new_ad_unit = AdUnit(
            name=data["name"],
            ad_unit_id=data["ad_unit_id"],
            ad_format=data["ad_format"],
            is_active=data.get("is_active", True)
        )
        db.session.add(new_ad_unit)
        db.session.commit()
        log_security_event("admin_action", f"Admin created AdSense ad unit: {new_ad_unit.name}", "info", user_id=request.token_payload["user_id"])
        return jsonify(new_ad_unit.to_dict()), 201
    except KeyError as e:
        return jsonify({"error": f"Missing or invalid field: {e}"}), 400
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error creating AdSense ad unit: {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/adsense/ad-units", methods=["GET"])
@token_required
@admin_required
def get_all_ad_units_admin():
    """Retorna todas as unidades de anúncio."""
    ad_units = AdUnit.query.all()
    return jsonify([au.to_dict() for au in ad_units])

@admin_bp.route("/adsense/ad-units/<int:ad_unit_id>", methods=["PUT"])
@token_required
@admin_required
def update_ad_unit_admin(ad_unit_id):
    """Atualiza uma unidade de anúncio existente."""
    ad_unit = AdUnit.query.get(ad_unit_id)
    if not ad_unit:
        return jsonify({"error": "Ad unit not found"}), 404

    data = request.get_json()
    try:
        ad_unit.name = data.get("name", ad_unit.name)
        ad_unit.ad_unit_id = data.get("ad_unit_id", ad_unit.ad_unit_id)
        ad_unit.ad_format = data.get("ad_format", ad_unit.ad_format)
        ad_unit.is_active = data.get("is_active", ad_unit.is_active)

        db.session.commit()
        log_security_event("admin_action", f"Admin updated AdSense ad unit: {ad_unit.name} (ID: {ad_unit.id})", "info", user_id=request.token_payload["user_id"])
        return jsonify(ad_unit.to_dict())
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error updating AdSense ad unit (ID: {ad_unit_id}): {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/adsense/ad-units/<int:ad_unit_id>", methods=["DELETE"])
@token_required
@admin_required
def delete_ad_unit_admin(ad_unit_id):
    """Deleta uma unidade de anúncio."""
    ad_unit = AdUnit.query.get(ad_unit_id)
    if not ad_unit:
        return jsonify({"error": "Ad unit not found"}), 404

    try:
        db.session.delete(ad_unit)
        db.session.commit()
        log_security_event("admin_action", f"Admin deleted AdSense ad unit: {ad_unit.name} (ID: {ad_unit.id})", "info", user_id=request.token_payload["user_id"])
        return jsonify({"message": "Ad unit deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error deleting AdSense ad unit (ID: {ad_unit_id}): {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

# --- Player Management ---
@admin_bp.route("/players", methods=["GET"])
@token_required
@admin_required
def get_all_players():
    """Retorna todos os jogadores com paginação e filtros."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    username = request.args.get("username")
    min_level = request.args.get("min_level", type=int)
    max_level = request.args.get("max_level", type=int)

    query = Player.query.join(User)

    if username:
        query = query.filter(User.username.ilike(f"%{username}%"))
    if min_level:
        query = query.filter(Player.level >= min_level)
    if max_level:
        query = query.filter(Player.level <= max_level)

    players = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "players": [p.to_dict() for p in players.items],
        "total_players": players.total,
        "total_pages": players.pages,
        "current_page": players.page
    })

@admin_bp.route("/players/<int:player_id>", methods=["GET"])
@token_required
@admin_required
def get_player(player_id):
    """Retorna um jogador específico pelo ID."""
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404
    return jsonify(player.to_dict())

@admin_bp.route("/players/<int:player_id>", methods=["PUT"])
@token_required
@admin_required
def update_player(player_id):
    """Atualiza um jogador existente."""
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    data = request.get_json()
    try:
        player.level = data.get("level", player.level)
        player.health = data.get("health", player.health)
        player.power = data.get("power", player.power)
        player.wallet_balance = str(data.get("wallet_balance", player.wallet_balance))
        player.monsters_killed = data.get("monsters_killed", player.monsters_killed)
        player.players_killed = data.get("players_killed", player.players_killed)
        player.deaths = data.get("deaths", player.deaths)
        player.current_phase = data.get("current_phase", player.current_phase)

        db.session.commit()
        log_security_event("admin_action", f"Admin updated player: {player.user.username} (ID: {player.id})", "info", user_id=request.token_payload["user_id"])
        return jsonify(player.to_dict())
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error updating player (ID: {player_id}): {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/players/<int:player_id>/give-item", methods=["POST"])
@token_required
@admin_required
def give_item_to_player(player_id):
    """Dá um item a um jogador."""
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    data = request.get_json()
    item_id = data.get("item_id")
    quantity = data.get("quantity", 1)

    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    try:
        inventory_item = InventoryItem.query.filter_by(player_id=player.id, item_id=item.id).first()
        if inventory_item:
            inventory_item.quantity += quantity
        else:
            inventory_item = InventoryItem(player_id=player.id, item_id=item.id, quantity=quantity)
            db.session.add(inventory_item)
        db.session.commit()
        log_security_event("admin_action", f"Admin gave {quantity}x {item.name} to player {player.user.username}", "info", user_id=request.token_payload["user_id"])
        return jsonify({"message": f"Successfully gave {quantity}x {item.name} to {player.user.username}"}), 200
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error giving item to player {player_id}: {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/players/<int:player_id>/give-card", methods=["POST"])
@token_required
@admin_required
def give_card_to_player(player_id):
    """Dá uma carta colecionável a um jogador."""
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    data = request.get_json()
    card_id = data.get("card_id")
    quantity = data.get("quantity", 1)

    card = CollectibleCard.query.get(card_id)
    if not card:
        return jsonify({"error": "Collectible card not found"}), 404

    try:
        player_card = PlayerCollectibleCard.query.filter_by(player_id=player.id, card_id=card.id).first()
        if player_card:
            player_card.quantity += quantity
        else:
            player_card = PlayerCollectibleCard(player_id=player.id, card_id=card.id, quantity=quantity)
            db.session.add(player_card)
        db.session.commit()
        log_security_event("admin_action", f"Admin gave {quantity}x {card.name} to player {player.user.username}", "info", user_id=request.token_payload["user_id"])
        return jsonify({"message": f"Successfully gave {quantity}x {card.name} to {player.user.username}"}), 200
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error giving card to player {player_id}: {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/players/<int:player_id>/remove-item", methods=["POST"])
@token_required
@admin_required
def remove_item_from_player(player_id):
    """Remove um item do inventário de um jogador."""
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    data = request.get_json()
    item_id = data.get("item_id")
    quantity = data.get("quantity", 1)

    inventory_item = InventoryItem.query.filter_by(player_id=player.id, item_id=item_id).first()
    if not inventory_item:
        return jsonify({"error": "Item not found in player\'s inventory"}), 404

    try:
        if inventory_item.quantity <= quantity:
            db.session.delete(inventory_item)
            message = f"Successfully removed all {inventory_item.item.name} from {player.user.username}"
        else:
            inventory_item.quantity -= quantity
            message = f"Successfully removed {quantity}x {inventory_item.item.name} from {player.user.username}"
        db.session.commit()
        log_security_event("admin_action", message, "info", user_id=request.token_payload["user_id"])
        return jsonify({"message": message}), 200
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error removing item from player {player_id}: {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/players/<int:player_id>/remove-card", methods=["POST"])
@token_required
@admin_required
def remove_card_from_player(player_id):
    """Remove uma carta colecionável de um jogador."""
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    data = request.get_json()
    card_id = data.get("card_id")
    quantity = data.get("quantity", 1)

    player_card = PlayerCollectibleCard.query.filter_by(player_id=player.id, card_id=card_id).first()
    if not player_card:
        return jsonify({"error": "Collectible card not found in player\'s collection"}), 404

    try:
        if player_card.quantity <= quantity:
            db.session.delete(player_card)
            message = f"Successfully removed all {player_card.card.name} from {player.user.username}"
        else:
            player_card.quantity -= quantity
            message = f"Successfully removed {quantity}x {player_card.card.name} from {player.user.username}"
        db.session.commit()
        log_security_event("admin_action", message, "info", user_id=request.token_payload["user_id"])
        return jsonify({"message": message}), 200
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error removing card from player {player_id}: {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

# --- Shop Item Management ---
@admin_bp.route("/shop-items", methods=["POST"])
@token_required
@admin_required
def create_shop_item():
    """Adiciona um item à loja."""
    data = request.get_json()
    try:
        item_id = data["item_id"]
        item = Item.query.get(item_id)
        if not item:
            return jsonify({"error": "Item not found"}), 404

        new_shop_item = ShopItem(
            item_id=item_id,
            price=str(data["price"]),
            discount_percentage=data.get("discount_percentage", 0.0),
            is_featured=data.get("is_featured", False),
            is_available=data.get("is_available", True),
            stock_quantity=data.get("stock_quantity"),
            required_level=data.get("required_level", 1),
            required_phase=data.get("required_phase", 1)
        )
        db.session.add(new_shop_item)
        db.session.commit()
        log_security_event("admin_action", f"Admin added item {item.name} to shop", "info", user_id=request.token_payload["user_id"])
        return jsonify(new_shop_item.to_dict()), 201
    except KeyError as e:
        return jsonify({"error": f"Missing field: {e}"}), 400
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error adding item to shop: {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/shop-items", methods=["GET"])
@token_required
@admin_required
def get_all_shop_items():
    """Retorna todos os itens da loja com paginação e filtros."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    item_name = request.args.get("item_name")
    is_available = request.args.get("is_available", type=bool)

    query = ShopItem.query.join(Item)

    if item_name:
        query = query.filter(Item.name.ilike(f"%{item_name}%"))
    if is_available is not None:
        query = query.filter(ShopItem.is_available == is_available)

    shop_items = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "shop_items": [si.to_dict() for si in shop_items.items],
        "total_shop_items": shop_items.total,
        "total_pages": shop_items.pages,
        "current_page": shop_items.page
    })

@admin_bp.route("/shop-items/<int:shop_item_id>", methods=["PUT"])
@token_required
@admin_required
def update_shop_item(shop_item_id):
    """Atualiza um item da loja existente."""
    shop_item = ShopItem.query.get(shop_item_id)
    if not shop_item:
        return jsonify({"error": "Shop item not found"}), 404

    data = request.get_json()
    try:
        shop_item.price = str(data.get("price", shop_item.price))
        shop_item.discount_percentage = data.get("discount_percentage", shop_item.discount_percentage)
        shop_item.is_featured = data.get("is_featured", shop_item.is_featured)
        shop_item.is_available = data.get("is_available", shop_item.is_available)
        shop_item.stock_quantity = data.get("stock_quantity", shop_item.stock_quantity)
        shop_item.required_level = data.get("required_level", shop_item.required_level)
        shop_item.required_phase = data.get("required_phase", shop_item.required_phase)

        db.session.commit()
        log_security_event("admin_action", f"Admin updated shop item (ID: {shop_item.id})", "info", user_id=request.token_payload["user_id"])
        return jsonify(shop_item.to_dict())
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error updating shop item (ID: {shop_item_id}): {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/shop-items/<int:shop_item_id>", methods=["DELETE"])
@token_required
@admin_required
def delete_shop_item(shop_item_id):
    """Remove um item da loja."""
    shop_item = ShopItem.query.get(shop_item_id)
    if not shop_item:
        return jsonify({"error": "Shop item not found"}), 404

    try:
        db.session.delete(shop_item)
        db.session.commit()
        log_security_event("admin_action", f"Admin deleted shop item (ID: {shop_item.id})", "info", user_id=request.token_payload["user_id"])
        return jsonify({"message": "Shop item deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        log_security_event("admin_action_error", f"Error deleting shop item (ID: {shop_item_id}): {e}", "error", user_id=request.token_payload["user_id"])
        return jsonify({"error": str(e)}), 500



