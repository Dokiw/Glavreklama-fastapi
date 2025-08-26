Glavreklama-fastapi

Базовый (boilerplate) проект на FastAPI, который можно быстро переиспользовать как стартовую точку для реального приложения.
В этом проекте была попытка реализовать структуру и паттерны, близкие к production: модульная архитектура, разграничение слоёв (роутеры / зависимости / сервисы / Unit of Work / CRUD / модели), миграции базы (alembic) и Pydantic-схемы для валидации.

Ключевые идеи и возможности
Модульность — каждый модуль (например, auth, session, pay, constructions) оформлен как набор файлов:
router.py — маршруты/эндпоинты,
dependencies.py — зависимости FastAPI (Depends),
service.py — бизнес-логика,
UOW.py / unit_of_work.py — Unit of Work / транзакции,
crud / interfaces.py — доступ к БД через репозитории,
schemas.py, dto.py — Pydantic-схемы / DTO.

Чёткое разделение слоёв: Router → Dependencies → Service → UoW / Interfaces → CRUD → Models.
Pydantic — строгая валидация входящих/исходящих данных и автогенерация OpenAPI-документации.
Alembic — заготовка для миграций БД (папка alembic).
app/core содержит базовые абстракции и конфигурацию (например, интерфейс UoW).
app/db — конфигурация сессии SQLAlchemy и базовые модели.

Быстрый старт (пример)
Ниже — корректный, но общий набор команд. Подставь свои значения и проверь requirements.txt / pyproject.toml в репозитории.
Создать виртуальное окружение и установить зависимости:

python -m venv .venv
source .venv/bin/activate    # или .venv\Scripts\activate на Windows
pip install -r requirements.txt
Настроить .env (пример переменных — подставь те, что используются в config.py):
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
SECRET_KEY=your_secret_key
# другие переменные окружения
Запустить миграции:
alembic upgrade head

Запустить приложение:
uvicorn main:app --reload
# или, если точка входа в папке app: uvicorn app.main:app --reload
Открыть документацию OpenAPI:
http://127.0.0.1:8000/docs

Структура проекта (кратко)
.
├─ .venv
├─ alembic/                # миграции
├─ app/
│  ├─ core/
│  │  ├─ abs/              # абстракции (unit_of_work и т.п.)
│  │  └─ config.py
│  ├─ db/
│  │  ├─ migration/
│  │  ├─ base.py
│  │  └─ session.py
│  ├─ handlers/
│  │  ├─ auth/
│  │  │  ├─ router.py
│  │  │  ├─ dependencies.py
│  │  │  ├─ service.py
│  │  │  ├─ UOW.py
│  │  │  ├─ crud/
│  │  │  └─ schemas.py
│  │  └─ ... (session, pay, constructions ...)
│  ├─ models/
│  └─ main.py
├─ README.md
└─ ...

Как добавлять новый модуль
Создать папку app/handlers/<module_name>.

Добавить:
router.py — маршруты,
dependencies.py — зависимости (внедряемые через Depends),
service.py — бизнес-логику,
UOW.py / репозитории в crud/ — слой доступа к данным,
schemas.py / dto.py — Pydantic-схемы.
Подключить роутер в main.py (или автоподключение если реализовано).
Такой шаблон позволяет минимально изменяя код подключать новый функционал.

Рекомендации и возможные улучшения
Тесты: добавить модульные тесты для сервисов и интеграционные тесты для основных эндпоинтов. Покрытие критичных кейсов (аутентификация, транзакции).
CI / CD: настроить GitHub Actions для запуска тестов, линтинга и сборки.
Документация: расширить README: примеры запросов, описание env-переменных, описание схем и эндпоинтов.
Central services: вынести общие зависимости (логирование, почта, кеширование) в app/core/services чтобы избежать дублирования.
Повышение стабильности UoW: добавить тесты для сценариев с откатом/коммитом транзакций.
Примеры миграций: добавить пару реальных миграций и инструкции по локальному запуску БД (docker-compose).
Линтинг и форматирование: настроить pre-commit, black, ruff/flake8.
