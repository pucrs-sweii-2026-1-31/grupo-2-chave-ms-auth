import os
import logging
import sys
from flask import Flask, request
from flask_cors import CORS
from flasgger import Swagger
from .config import Config, Development, Production
from .services.db import db
from .routes import auth as auth_blueprint


def create_app():
    # Determine environment
    env = os.getenv('NODE_ENV', 'production')
    config_obj = Production
    log_level = logging.INFO

    if env == 'development':
        config_obj = Development
        log_level = logging.DEBUG

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout,
        force=True  # Ensure logging is reconfigured
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Starting MS Auth API in {env} mode...")

    app = Flask(__name__)
    app.config.from_object(config_obj)

    @app.before_request
    def log_request_info():
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("--- Incoming Request ---")
            logger.debug(f"Method: {request.method}")
            logger.debug(f"Path: {request.path}")
            logger.debug(f"Headers: {dict(request.headers)}")
            if request.is_json:
                logger.debug(f"Payload: {request.get_json(silent=True)}")
            logger.debug("------------------------")

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
