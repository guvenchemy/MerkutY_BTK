from logging.config import fileConfig
import os
from dotenv import load_dotenv

from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool

from alembic import context

# Load environment variables from .env file
load_dotenv()

# Import our models
from app.models.user_vocabulary import Base
from app.models import User, Vocabulary, UserVocabulary, ProcessedTranscript, UrlContent, UnknownWord, WordDefinition, UserGrammarKnowledge, GrammarPattern
from app.core.database import get_db

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the sqlalchemy.url from environment variable
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Ensure we use psycopg3 driver for SQLAlchemy 2.0+
    if database_url.startswith("postgresql://") and "+psycopg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    config.set_main_option("sqlalchemy.url", database_url)
    print(f"✅ Loaded DATABASE_URL from .env: {database_url}")
else:
    print("⚠️  Warning: DATABASE_URL not found in environment variables!")
    print("   Make sure you have a .env file with DATABASE_URL set")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Get the URL that we set from environment variable
    url = config.get_main_option("sqlalchemy.url")
    print(f"🗄️  Using database URL for offline migrations: {url}")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get DATABASE_URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    # Ensure we use psycopg3 driver for SQLAlchemy 2.0+
    if database_url.startswith("postgresql://") and "+psycopg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    print(f"✅ Using DATABASE_URL for Alembic: {database_url}")
    
    # Create engine directly with the DATABASE_URL
    connectable = create_engine(
        database_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
