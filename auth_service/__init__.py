from flask import Flask
from .config import Config
from .services.db import db
from .routes import auth as auth_blueprint


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    app.register_blueprint(auth_blueprint)

    with app.app_context():
        db.create_all()

    return app
