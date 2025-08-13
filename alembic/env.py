import sys
from pathlib import Path
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

# --- гарантируем, что корень проекта в sys.path (чтобы import app.* работал) ---
HERE = Path(__file__).resolve()
PROJECT_ROOT = HERE.parents[1]  # если alembic/ в корне проекта
sys.path.insert(0, str(PROJECT_ROOT))

# логгирование
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# импортируем Base и helper
from app.db.base import Base, import_all_models
from app.core.config import settings  # если используешь settings

# Импортируем все модели до получения target_metadata
import_all_models("app.models")

# DEBUG: можно временно включить, затем убрать
print("=== ALEMBIC DEBUG ===")
print(f"Tables in metadata: {list(Base.metadata.tables.keys())}")
print("=== END DEBUG ===")

target_metadata = Base.metadata

# Переопределяем URL из settings (если нужно)
database_url = (
    f"postgresql+psycopg2://"
    f"{settings.DB_USER}:{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)
config.set_main_option("sqlalchemy.url", database_url)

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        {"sqlalchemy.url": database_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
