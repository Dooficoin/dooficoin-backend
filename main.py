import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from database import db
from routes.user import user_bp
from routes.game import game_bp
from routes.wallet import wallet_bp
from routes.security import security_bp
from routes.mining import mining_bp
from routes.adsense import adsense_bp
from routes.ad_status import ad_status_bp
from routes.level import level_bp
from routes.scenario import scenario_bp
from routes.admin import admin_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dooficoin-frontend', 'dist'), static_url_path='/')

# Habilitar CORS para todas as rotas
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(game_bp, url_prefix='/api/game')
app.register_blueprint(wallet_bp, url_prefix='/api/wallet')
app.register_blueprint(security_bp, url_prefix='/api/security')
app.register_blueprint(mining_bp, url_prefix='/api/mining')
app.register_blueprint(adsense_bp, url_prefix="/api/adsense")
app.register_blueprint(ad_status_bp, url_prefix="/api/ads")
app.register_blueprint(level_bp, url_prefix="/api/level")
app.register_blueprint(scenario_bp, url_prefix="/api/scenarios")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Importar todos os modelos para garantir que sejam registrados
from models.user import User
from models.player import Player
from models.security_log import SecurityLog, FraudAlert, LoginAttempt, BlockedIP
from models.mining import MiningSession, MiningReward, MiningStatistics
from models.adsense import AdSenseConfig, AdUnit, AdDisplay, AdRevenue
from models.item import Item, InventoryItem, ShopItem, CollectibleCard, PlayerCollectibleCard, ItemDrop
from models.level import PlayerLevel, LevelReward, PhaseProgress
from models.scenario import Scenario, Monster, ScenarioReward, PlayerScenarioProgress

with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)