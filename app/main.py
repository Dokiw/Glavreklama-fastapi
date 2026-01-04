import importlib
import importlib.util
import json
import logging
import os
import pkgutil
import sys
import time
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🚀 выполняется при старте
    import_all_routes(app, "app.handlers")

    yield  # ← здесь приложение работает

    # 🛑 выполняется при завершении
    # можно добавить, например, закрытие соединений с БД


app = FastAPI(
    lifespan=lifespan,
    root_path="/v1/main"
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:9787",
    "https://glavprojects.ru",
    "https://catcheggsapp.web.app",
    "https://admin.glavprojects.ru",
    "http://185.133.42.31",
    "*"
]

# Подключаем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOG_DIR = "/var/log/fastapi"
LOG_FILE = os.path.join(LOG_DIR, "log.txt")
MAX_BODY_SNIPPET = 200  # сколько символов тела логировать

# простая инициализация каталога/файла
os.makedirs(LOG_DIR, exist_ok=True)


# убедитесь, что пользователь запускающего процесса может писать в этот каталог:
# sudo chown -R <user>:<group> /var/log/fastapi

def mask_headers(h: dict) -> dict:
    out = {}
    for k, v in h.items():
        if k.lower() == "authorization":
            out[k] = "<masked>"
        else:
            out[k] = v
    return out


def append_log(obj: dict):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception:
        # если лог не пишется — не ломаем приложение
        pass


@app.middleware("http")
async def simple_logger_middleware(request: Request, call_next):
    start = time.time()

    # прочитать тело запроса и восстановить stream для endpoint
    try:
        body_bytes = await request.body()
    except Exception:
        body_bytes = b""

    async def receive():
        return {"type": "http.request", "body": body_bytes}

    # восстановление для дальнейшего использования в обработчике
    request._receive = receive  # работает в FastAPI/Starlette

    client_ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else None)
    headers = dict(request.headers)
    headers = mask_headers(headers)
    qs = dict(request.query_params)
    body_snippet = None
    if body_bytes:
        try:
            text = body_bytes.decode("utf-8", errors="replace")
            body_snippet = text[:MAX_BODY_SNIPPET]
            if len(text) > MAX_BODY_SNIPPET:
                body_snippet += " ...(truncated)"
        except Exception:
            body_snippet = f"<{len(body_bytes)} bytes>"

    req_log = {
        "event": "request.start",
        "ts": int(start),
        "method": request.method,
        "path": str(request.url.path),
        "url": str(request.url),
        "client_ip": client_ip,
        "headers": headers,
        "query": qs,
        "body_snippet": body_snippet,
    }
    append_log(req_log)

    try:
        response = await call_next(request)
        duration = time.time() - start

        resp_log = {
            "event": "request.end",
            "ts": int(time.time()),
            "method": request.method,
            "path": str(request.url.path),
            "status_code": response.status_code,
            "duration_s": round(duration, 3),
            "response_content_length": response.headers.get("content-length"),
        }
        append_log(resp_log)
        return response

    except Exception as ex:
        duration = time.time() - start
        err_log = {
            "event": "request.exception",
            "ts": int(time.time()),
            "method": request.method,
            "path": str(request.url.path),
            "duration_s": round(duration, 3),
            "error": str(ex),
            "traceback": traceback.format_exc(),
        }
        append_log(err_log)
        raise


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
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=9787, timeout_keep_alive=120)
