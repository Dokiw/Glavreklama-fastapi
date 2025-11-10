from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery = Celery(
    "billing",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["task_celery.pay_task.task"],
)

celery.conf.update(
    timezone="Europe/Moscow",  # важно: указать TZ
    enable_utc=False,         # используем локальную часовую зону (можно True + UTC crontab)
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery.conf.beat_schedule = {
    "daily-auto-payment-03-00": {
        "task": "tasks.run_auto_payment",          # имя задачи в tasks.py
        "schedule": crontab(hour=3, minute=0),     # каждый день в 03:00 Europe/Moscow
        "options": {"queue": "billing"},           # опционально: очередь для billing
    },
}

celery.conf.timezone = "Europe/Moscow"