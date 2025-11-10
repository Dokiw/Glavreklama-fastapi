import json
from functools import wraps
from fastapi import HTTPException, status

from app.main import logger


def _safe_str(obj, max_len=200):
    """Безопасно привести объект к строке для логов."""
    try:
        # сначала пробуем JSON (удобно для dict/list)
        return json.dumps(obj, default=str, ensure_ascii=False)[:max_len]
    except Exception:
        try:
            return repr(obj)[:max_len]
        except Exception:
            return f"<unserializable {type(obj).__name__}>"


def transactional(uow_attr: str = "uow"):
    """
    Декоратор для запуска функции в транзакции.
    :param uow_attr: имя атрибута (по умолчанию self.uow)
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            self = args[0]
            uow = getattr(self, uow_attr)
            try:
                async with uow:
                    return await func(*args, **kwargs)

            except HTTPException:
                # не перехватываем HTTP ошибки — пробрасываем выше
                raise

            except Exception as e:

                api_payment = kwargs.get("api_payment", None)
                if api_payment is None:
                    api_payment = getattr(self, "api_payment", None)

                # Логируем исключение с полным стеком и безопасным представлением api_payment
                logger.exception(
                    "Unhandled exception in %s. api_payment=%s",
                    func.__qualname__,
                    _safe_str(api_payment)
                )

                # любые другие ошибки — откатываем транзакцию и возвращаем 500
                #raise HTTPException(
                #    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                #    detail=f"Внутренняя ошибка сервера: {str(e)}"
                #)

        return wrapper

    return decorator
