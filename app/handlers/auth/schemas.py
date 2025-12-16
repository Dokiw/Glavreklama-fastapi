from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

from app.handlers.providers.schemas import ProviderOut, ProviderLoginRequest


# ---- Request / Input ----
class UserCreate(BaseModel):
    user_name: str = Field(..., alias="UserName")
    email: Optional[EmailStr] = None
    password: str = Field(..., alias="UserPass")
    first_name: Optional[str] = Field(None, alias="FirstName")
    last_name: Optional[str] = Field(None, alias="LastName")
    meta_data: Optional[Dict[str, Any]] = Field(None, alias="MetaData")

    class Config:
        validate_by_name = True
        # todo можно добавить валидации/регулярки для username, длину пароля и т.д.


class UserUpdate(BaseModel):
    user_id: int = Field(...)
    user_name: Optional[str] = Field(None)
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    meta_data: Optional[Dict[str, Any]] = Field(None)

    class Config:
        validate_by_name = True
        # todo можно добавить валидации/регулярки для username, длину пароля и т.д.


class UserCreateProvide(UserCreate):
    user_name: str = Field(..., alias="UserName")
    email: Optional[EmailStr] = Field(None, alias="Email")
    password: Optional[str] = Field(None, alias="UserPass")
    first_name: Optional[str] = Field(None, alias="FirstName")
    last_name: Optional[str] = Field(None, alias="LastName")

    class Config:
        validate_by_name = True
        # todo можно добавить валидации/регулярки для username, длину пароля и т.д.


class LogInUser(BaseModel):
    username: str = Field(..., alias="UserName")
    password: str = Field(..., alias="UserPass")

    class Config:
        validate_by_name = True


class LogInUserBot(BaseModel):
    username: str = Field(..., alias="UserName")
    provider_user_id: int = Field(..., alias="ProviderUserId")

    client_id: Optional[str] = Field(None, alias="ClientId")
    client_secret: Optional[str] = Field(None, alias="ClientSecret")

    class Config:
        validate_by_name = True


class InitDataRequest(BaseModel):
    init_data: str


class LogOutUser(BaseModel):
    user_id: int = Field(..., alias="UserId")

    class Config:
        validate_by_name = True


# ---- Response / Output ----
class OutUser(BaseModel):
    id: int = Field(..., alias="UserId")
    username: str = Field(..., alias="UserName")
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, alias="FirstName")
    last_name: Optional[str] = Field(None, alias="LastName")
    role_id: Optional[int] = Field(None, alias="RoleId")

    class Config:
        validate_by_name = True
        from_attributes = True


class RoleUser(BaseModel):
    role_id: Optional[int] = Field(None, alias="RoleId")
    name: str
    description: Optional[str] = None

    class Config:
        validate_by_name = True
        from_attributes = True


class PaginateUser(BaseModel):
    users: List[OutUser]
    total: int
    Offset_current: int


# --- Auth / Tokens ---

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None  # seconds


class AuthResponse(BaseModel):
    user_data: OutUser = Field(..., alias="UserData")
    token: Token = Field(..., alias="UserToken")

    class Config:
        from_attributes = True
        validate_by_name = True


class AuthResponseProvide(BaseModel):
    user_data: OutUser = Field(..., alias="UserData")
    token: Token = Field(..., alias="UserToken")
    provide_data: ProviderOut = Field(..., alias="ProvideData")

    class Config:
        from_attributes = True
        validate_by_name = True
