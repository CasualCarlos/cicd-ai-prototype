"""Flask application factory. (v2.0)"""

from flask import Flask, jsonify

from app.database import close_db, init_db
from app.routes.users import users_bp
from app.routes.products import products_bp


def create_app(config=None):
    """Create and configure the Flask application.

    Args:
        config: Optional mapping of configuration overrides.
                Defaults to a file-based SQLite database.
    """
    app = Flask(__name__)

    # Default configuration
    app.config.setdefault("DATABASE", "app.db")
    app.config.setdefault("TESTING", False)

    if config:
        app.config.update(config)

    # Register teardown
    app.teardown_appcontext(close_db)

    # Initialise schema
    init_db(app)

    # Register blueprints
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(products_bp, url_prefix="/products")

    @app.route("/")
    def health():
        return jsonify({"status": "ok"})

    return app
