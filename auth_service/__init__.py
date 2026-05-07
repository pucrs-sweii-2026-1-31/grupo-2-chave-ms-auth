from flask import Flask

from .config import Config
from .extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Extensões
    db.init_app(app)

    # Blueprints
    from .routes.auth import auth_bp

    app.register_blueprint(auth_bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app
