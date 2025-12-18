from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.handlers.providers.schemas import ProviderOut, ProviderLoginRequest


# ---- Request / Input ----
class UserCreate(BaseModel):
    user_name: str = Field(..., alias="userName")
    email: Optional[EmailStr] = None
    password: str = Field(..., alias="passUser")
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    meta_data: Optional[Dict[str, Any]] = Field(None, alias="metaData")

    class Config:
        validate_by_name = True
        # todo можно добавить валидации/регулярки для username, длину пароля и т.д.


class UserUpdate(BaseModel):
    user_id: int = Field(...)
    user_name: Optional[str] = Field(None)
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    meta_data: Optional[Dict[str, Any]] = Field(None)
    email: Optional[EmailStr] = Field(None)

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value):
        if value is None:
            return value

        if isinstance(value, str):
            value = value.strip().lower()

        if not value:
            raise ValueError("Email must not be empty")

        return value

    class Config:
        validate_by_name = True


class UserCreateProvide(UserCreate):
    user_name: str = Field(..., alias="userName")
    email: Optional[EmailStr] = Field(None, alias="email")
    password: Optional[str] = Field(None, alias="passUser")
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")

    class Config:
        validate_by_name = True
        # todo можно добавить валидации/регулярки для username, длину пароля и т.д.


class LogInUser(BaseModel):
    username: str = Field(..., alias="userName")
    password: str = Field(..., alias="passUser")

    class Config:
        validate_by_name = True


class LogInUserBot(BaseModel):
    username: str = Field(..., alias="userName")
    provider_user_id: int = Field(..., alias="providerUserId")

    client_id: Optional[str] = Field(None, alias="clientId")
    client_secret: Optional[str] = Field(None, alias="clientSecret")

    class Config:
        validate_by_name = True


class InitDataRequest(BaseModel):
    init_data: str


class LogOutUser(BaseModel):
    user_id: int = Field(..., alias="idUser")

    class Config:
        validate_by_name = True


# ---- Response / Output ----
class OutUser(BaseModel):
    id: int = Field(..., alias="idUser")
    username: str = Field(..., alias="user")
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
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
    user_data: OutUser = Field(..., alias="userData")
    token: Token = Field(..., alias="tokenUser")

    class Config:
        from_attributes = True
        validate_by_name = True


class AuthResponseProvide(BaseModel):
    user_data: OutUser = Field(..., alias="userData")
    token: Token = Field(..., alias="tokenUser")
    provide_data: ProviderOut = Field(..., alias="provideData")

    class Config:
        from_attributes = True
        validate_by_name = True
