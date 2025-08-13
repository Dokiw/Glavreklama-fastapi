# debug_imports.py — положи в корень проекта и запусти: python debug_imports.py
import sys, traceback
from pathlib import Path

print("CWD:", Path.cwd())
print("Python:", sys.version)
print("sys.path (head):")
for p in sys.path[:5]:
    print("  ", p)

try:
    from app.db.base import import_all_models, Base, get_all_model_classes
except Exception as e:
    print("ERROR importing app.db.base:", e)
    traceback.print_exc()
    raise SystemExit(1)

print("\n-> Проверяем пакет app.models ...")
import importlib, pkgutil
try:
    pkg = importlib.import_module("app.models")
    print("app.models found; __path__:", getattr(pkg, "__path__", None))
    subs = list(pkgutil.iter_modules(pkg.__path__))
    print("subpackages in app.models:", [s[1] for s in subs])
except ModuleNotFoundError:
    print("app.models NOT found. Проверь sys.path / рабочую директорию.")
    raise SystemExit(1)

print("\n-> Вызов import_all_models('app.models') ...")
import_all_models("app.models")

print("\nBase.metadata tables keys:", list(Base.metadata.tables.keys()))
print("Mapped classes via Base.registry:", [m.class_.__name__ for m in Base.registry.mappers])

print("\n-> Доп. проверка: импортируем каждый app.models.<subpkg>.models")
for finder, name, ispkg in subs:
    module_name = f"app.models.{name}.models"
    try:
        mod = importlib.import_module(module_name)
        print(f" Imported {module_name}")
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if isinstance(obj, type):
                try:
                    is_sub = issubclass(obj, Base) and obj is not Base
                except TypeError:
                    is_sub = False
                if is_sub:
                    print(f"   model: {obj.__name__} (tablename={getattr(obj,'__tablename__',None)})")
    except ModuleNotFoundError:
        print(f"  -> no {module_name} (models.py missing)")
    except Exception as e:
        print(f"  -> error importing {module_name}: {e}")
        traceback.print_exc()
