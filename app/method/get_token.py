from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.models import APIKey

bearer_scheme = HTTPBearer(auto_error=False)  # auto_error=False чтобы можно было вручную бросать 401


async def get_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    token = credentials.credentials

    # Здесь можно добавить проверку JWT или любую асинхронную проверку токена
    # await some_async_verification(token)

    return token
