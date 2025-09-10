
from typing import Protocol, List, Optional, Dict, Any
from app.handlers.auth.schemas import (
    RoleUser,
    OutUser,
    UserCreate,
    LogInUser,
    AuthResponse, AuthResponseProvide, UserCreateProvide
)
from app.handlers.auth.dto import UserAuthData
from app.handlers.providers.schemas import ProviderRegisterRequest, ProviderLoginRequest
from app.handlers.session.schemas import CheckSessionAccessToken



class AsyncWalletRepository(Protocol):

    async def create_wallet_user(self):
        ...
