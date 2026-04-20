"""Flask application factory."""
import os
from flask import Flask
from flasgger import Swagger
from flask_cors import CORS

from app.config import Config, get_config
from app.controllers import register_blueprints
from app.extensions import db


def create_app(config: Config = None) -> Flask:
    """Create and configure Flask application.

    Args:
        config: Configuration object. If None, uses get_config()

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Load configuration
    if config is None:
        config = get_config()

    app.config.from_object(config)
    
    allowed_origins = [
        "https://legion-combat-xwxxfbjoe-josecaro02s-projects.vercel.app"
    ]

    # Permitir localhost solo en desarrollo
    if os.getenv("FLASK_ENV") == "development":
        allowed_origins.append("http://localhost:5173")

    CORS(
        app,
        resources={r"/*": {"origins": allowed_origins}},
        supports_credentials=True
    )

    # Initialize extensions
    db.init_app(app)

    from app.commands import create_owner
    app.cli.add_command(create_owner)

    # Register blueprints
    register_blueprints(app)

    # Initialize Flasgger (Swagger)
    Swagger(app, template=config.get_swagger_template())

    # Register error handlers
    register_error_handlers(app)

    return app


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for the application."""

    @app.errorhandler(400)
    def bad_request(error):
        return {
            'error': 'BAD_REQUEST',
            'message': str(error.description)
        }, 400

    @app.errorhandler(401)
    def unauthorized(error):
        return {
            'error': 'UNAUTHORIZED',
            'message': 'Authentication required'
        }, 401

    @app.errorhandler(403)
    def forbidden(error):
        return {
            'error': 'FORBIDDEN',
            'message': 'Insufficient permissions'
        }, 403

    @app.errorhandler(404)
    def not_found(error):
        return {
            'error': 'NOT_FOUND',
            'message': 'Resource not found'
        }, 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return {
            'error': 'METHOD_NOT_ALLOWED',
            'message': 'Method not allowed'
        }, 405

    @app.errorhandler(500)
    def internal_error(error):
        return {
            'error': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }, 500


__all__ = ['create_app', 'db']
