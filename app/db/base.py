# app/db/base.py
from sqlalchemy.orm import DeclarativeBase
import importlib
import pkgutil
from typing import List

class Base(DeclarativeBase):
    """Declarative base (SQLAlchemy 2.0 style)."""
    pass

def import_all_models(package_name: str = "app.models") -> None:
    """
    Ищет подпакеты в package_name и пытается импортировать
    <package>.<subpkg>.models — если файл models.py есть в подпакете.
    Это гарантирует, что декларативные классы попадут в Base.metadata.
    """
    try:
        pkg = importlib.import_module(package_name)
    except ModuleNotFoundError:
        # пакет app.models не найден — ничего не делаем
        return

    if not hasattr(pkg, "__path__"):
        return

    for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__):
        # Попробуем импортировать модуль вида app.models.<name>.models
        module_name = f"{package_name}.{name}.models"
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            # Если в подпакете нет models.py, пропускаем
            continue
        except Exception as e:
            # Не рушим процесс; логируем для отладки
            print(f"[import_all_models] Ошибка при импорте {module_name}: {e}")

def get_all_model_classes() -> List[type]:
    """
    Возвращает список классов, смаппленных в текущем Base.registry (удобно для отладки).
    """
    return [m.class_ for m in Base.registry.mappers if hasattr(m.class_, "__tablename__")]
