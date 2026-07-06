"""Ambiente Alembic — duas trilhas de migration: schema e dados de referência (plano §3.3)."""
from alembic import context
from sqlalchemy import engine_from_config, pool

from giva.config import resolver_url_banco

config = context.config

# Política 12-factor única (ver giva.config): DATABASE_URL manda; a URL de dev
# do alembic.ini só entra sob opt-in ALEMBIC_ALLOW_INI_URL=1 (dev local).
config.set_main_option(
    "sqlalchemy.url",
    resolver_url_banco(fallback_ini=config.get_main_option("sqlalchemy.url")),
)

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
