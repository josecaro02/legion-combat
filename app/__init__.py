"""Flask application factory."""
from flask import Flask

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

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Create tables (for development only - use migrations in production)
    with app.app_context():
        db.create_all()

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
