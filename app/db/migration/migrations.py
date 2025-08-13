from alembic import command
from alembic.config import Config
from pathlib import Path
from .base import get_all_models

def create_migration(message: str = "auto migration"):
    """Создает новую миграцию"""
    # Путь к alembic.ini (предполагается, что он в корне проекта)
    project_root = Path(__file__).parent.parent.parent
    alembic_cfg = Config(project_root / "alembic.ini")
    
    # Создаем миграцию
    command.revision(alembic_cfg, message=message, autogenerate=True)

def upgrade_database(revision: str = "head"):
    """Применяет миграции к базе данных"""
    project_root = Path(__file__).parent.parent.parent
    alembic_cfg = Config(project_root / "alembic.ini")
    
    command.upgrade(alembic_cfg, revision)

def create_initial_migration():
    """Создает начальную миграцию со всеми таблицами"""
    # Импортируем все модели
    models = get_all_models()
    
    if models:
        print(f"Найдено {len(models)} моделей:")
        for model in models:
            print(f"  - {model.__name__} -> {model.__tablename__}")
        
        create_migration("Initial migration with all tables")
        print("Начальная миграция создана!")
    else:
        print("Модели не найдены!")