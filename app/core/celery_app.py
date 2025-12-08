from celery import Celery

celery_app = Celery(
    "project",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.autodiscover_tasks(["task_celery"])