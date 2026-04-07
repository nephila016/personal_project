import os

from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from app.database import db
from config import config_map

login_manager = LoginManager()
login_manager.login_view = "auth.login"
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])


def create_app(config_name: str | None = None) -> Flask:
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map["development"]))

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    CORS(app)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.global_admin import GlobalAdmin

        return db.session.get(GlobalAdmin, int(user_id))

    from web.auth.routes import auth_bp
    from web.dashboard.routes import dashboard_bp
    from web.api.orders import orders_api
    from web.api.customers import customers_api
    from web.api.admins import admins_api
    from web.api.inventory import inventory_api
    from web.api.stats import stats_api

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(orders_api)
    app.register_blueprint(customers_api)
    app.register_blueprint(admins_api)
    app.register_blueprint(inventory_api)
    app.register_blueprint(stats_api)

    with app.app_context():
        from app.models import Base  # noqa: F401

        db.create_all()

    return app
