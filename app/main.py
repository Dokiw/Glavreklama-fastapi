import importlib.util
import pkgutil
import sys
import traceback
from pathlib import Path
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
import importlib
import pkgutil
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🚀 выполняется при старте
    import_all_routes(app, "app.handlers")

    yield  # ← здесь приложение работает

    # 🛑 выполняется при завершении
    # можно добавить, например, закрытие соединений с БД



app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:9787",
    "https://glavprojects.ru",
    "https://catcheggsapp.web.app",
    "https://admin.glavprojects.ru",
]

# Подключаем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def import_all_routes(app: FastAPI, package_name: str):
    logger = __import__("logging").getLogger("uvicorn")
    try:
        pkg = importlib.import_module(package_name)
    except ModuleNotFoundError as e:
        logger.warning(f"Пакет {package_name} не найден: {e}")
        logger.debug("sys.path:\n" + "\n".join(repr(p) for p in sys.path))
        return
    except Exception as e:
        logger.error(f"Ошибка при импорте пакета {package_name}: {e}\n{traceback.format_exc()}")
        return

    # логируем путь, по которому пакет найден
    if not hasattr(pkg, "__path__"):
        logger.warning(f"{package_name} не является пакетом (нет __path__)")
        return

    pkg_paths = list(pkg.__path__)  # может быть несколько
    logger.info(f"{package_name}.__path__: {pkg_paths}")

    # для отладки — покажем содержимое каждой папки в __path__
    for p in pkg_paths:
        try:
            p_path = Path(p).resolve()
            listing = sorted([x.name for x in p_path.iterdir()])
            logger.info(f"Содержимое {p_path}: {listing}")
        except Exception as e:
            logger.warning(f"Не удалось прочитать {p}: {e}")

    # перечисляем подмодули (папки/файлы) и пытаемся импортировать {package}.{name}.router
    for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__):
        module_name = f"{package_name}.{name}.router"
        logger.debug(f"Попытка импортировать: {module_name} (ispkg={ispkg})")
        try:
            # быстрый pre-check: есть ли spec?
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                logger.debug(f"find_spec вернул None для {module_name}")
            else:
                logger.debug(f"spec.origin={getattr(spec, 'origin', None)}; loader={getattr(spec, 'loader', None)}")

            module = importlib.import_module(module_name)
            if hasattr(module, "router"):
                app.include_router(module.router)
                logger.info(f"✅ Подключен роутер: {module_name} → {module.router}")
            else:
                logger.warning(f"Модуль {module_name} импортирован, но не содержит 'router'")
        except ModuleNotFoundError as e:
            # подробный лог, чтоб понять, какой именно модуль не найден (имя в e.name)
            logger.warning(f"ModuleNotFoundError при импорте {module_name}: {e}; e.name={getattr(e, 'name', None)}")
            logger.debug(traceback.format_exc())
        except Exception as e:
            logger.error(f"[import_all_routes] Ошибка при импорте {module_name}: {e}\n{traceback.format_exc()}")




@app.get("/")
async def root()    :
    return {"message": "Hello World"}

if __name__ == "__main__":

    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9787)