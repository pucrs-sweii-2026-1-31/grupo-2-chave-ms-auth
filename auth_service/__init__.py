import logging
import sys
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from .config import Config
from .services.db import db
from .routes import auth as auth_blueprint


def create_app():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting MS Auth API...")

    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda model: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "MS Auth API",
            "description": "API para autenticação e gerenciamento de usuários.",
            "version": "1.0.0"
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\""
            }
        }
    }
    
    Swagger(app, config=swagger_config, template=swagger_template)
    db.init_app(app)
    app.register_blueprint(auth_blueprint)

    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created or already exist.")
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}", exc_info=True)

    return app
