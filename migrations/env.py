import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool

from alembic import context

# Agregar el directorio raíz al path para importar la aplicación
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Importar Base y los modelos para que Alembic detecte los metadatos
from app.extensions import Base
from app.models import *  # Importa todos los modelos

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadatos de los modelos para autogenerate
target_metadata = Base.metadata


def get_database_url():
    """Obtiene la URL de la base de datos desde variables de entorno."""
    # Intenta leer DATABASE_URL desde el entorno
    database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        # Si no está definida, usa la URL por defecto de desarrollo
        database_url = 'postgresql://postgres:postgres@localhost:5432/legion_combat_dev'
        print(f"ADVERTENCIA: DATABASE_URL no definida. Usando: {database_url}")

    return database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Configuración para SQLAlchemy 2.0
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Usar la URL de la base de datos desde el entorno
    database_url = get_database_url()

    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Configuración para SQLAlchemy 2.0
            render_as_batch=True,
            compare_type=True,  # Comparar tipos de columnas
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
