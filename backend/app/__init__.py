from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)

    from app.config import config_map
    app.config.from_object(config_map[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=app.config["CORS_ORIGINS"])

    from app.routes.clients import clients_bp
    from app.routes.gateway import gateway_bp
    from app.routes.stats import stats_bp

    app.register_blueprint(clients_bp, url_prefix="/api/clients")
    app.register_blueprint(gateway_bp, url_prefix="/api/gateway")
    app.register_blueprint(stats_bp, url_prefix="/api/stats")

    return app
