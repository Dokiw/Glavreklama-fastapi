from functools import wraps
from fastapi import HTTPException, status


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
                # любые другие ошибки — откатываем транзакцию и возвращаем 500
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Внутренняя ошибка сервера: {str(e)}"
                )

        return wrapper

    return decorator
