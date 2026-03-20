import os
from datetime import timedelta
from typing import Optional


class Config:
    """Base configuration class."""

    # Flask
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV: str = os.environ.get('FLASK_ENV', 'development')

    # Database
    SQLALCHEMY_DATABASE_URI: Optional[str] = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

    # JWT Configuration
    JWT_SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=7)
    JWT_ALGORITHM: str = 'HS256'

    # Security
    BCRYPT_LOG_ROUNDS: int = 12

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/legion_combat_dev'
    )
    BCRYPT_LOG_ROUNDS: int = 4  # Faster for development


class TestingConfig(Config):
    """Testing configuration."""

    TESTING: bool = True
    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URI: str = 'postgresql://postgres:postgres@localhost:5432/legion_combat_test'
    WTF_CSRF_ENABLED: bool = False
    BCRYPT_LOG_ROUNDS: int = 4
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(minutes=5)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(minutes=30)


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG: bool = False

    def __init__(self):
        """Validate production settings."""
        super().__init__()
        if not self.SECRET_KEY or self.SECRET_KEY == 'dev-secret-key-change-in-production':
            raise ValueError("SECRET_KEY must be set in production")
        if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY == 'jwt-secret-key-change-in-production':
            raise ValueError("JWT_SECRET_KEY must be set in production")
        if not self.SQLALCHEMY_DATABASE_URI:
            raise ValueError("DATABASE_URL must be set in production")


# Configuration dictionary
config_by_name: dict = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}


def get_config() -> Config:
    """Get configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)()
