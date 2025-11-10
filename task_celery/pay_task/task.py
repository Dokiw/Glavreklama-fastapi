import asyncio

from task_celery.celery_config import celery
from task_celery.pay_task.dependencies import build_subtraction_service

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


@celery.task(name="tasks.run_auto_payment", bind=True, acks_late=True)
def run_auto_payment(self):
    from app.main import logger

    async def _runner():
        service = await build_subtraction_service()
        try:
            return await service.auto_payment_service()
        finally:
            if hasattr(service, "dispose"):
                await service.dispose()

    try:
        return loop.run_until_complete(_runner())
    except Exception as exc:
        logger.exception("run_auto_payment failed: %s", exc)
        raise
