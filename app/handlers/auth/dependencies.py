# app/handlers/auth/dependencies.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.handlers.auth.crud import UserRepository, RoleRepository
from app.handlers.auth.service import SqlAlchemyAuth
from app.handlers.auth.interfaces import AsyncUserRepository, AsyncRoleRepository

def get_user_repo(db: AsyncSession = Depends(get_db)) -> AsyncUserRepository:
    return UserRepository(db)

def get_role_repo(db: AsyncSession = Depends(get_db)) -> AsyncRoleRepository:
    return RoleRepository(db)

def get_auth_service(
    user_repo: AsyncUserRepository = Depends(get_user_repo),
    role_repo: AsyncRoleRepository = Depends(get_role_repo),
) -> SqlAlchemyAuth:
    return SqlAlchemyAuth(user_repo, role_repo)

# alias для роутов (удобно)
AuthServiceDep = Annotated[SqlAlchemyAuth, Depends(get_auth_service)]
