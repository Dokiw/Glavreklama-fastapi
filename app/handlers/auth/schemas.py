from typing import Optional
from pydantic import BaseModel, EmailStr, Field

# ---- Request / Input ----
class UserCreate(BaseModel):
    username: str = Field(..., alias="user_name")
    email: Optional[EmailStr] = None
    password: str = Field(..., alias="passUser")
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")

    class Config:
        allow_population_by_field_name = True
        # можно добавить валидации/регулярки для username, длину пароля и т.д.

class LogInUser(BaseModel):
    username: str = Field(..., alias="userName")
    password: str = Field(..., alias="passUser")

    class Config:
        allow_population_by_field_name = True

class LogOutUser(BaseModel):
    user_id: int = Field(..., alias="idUser")

    class Config:
        allow_population_by_field_name = True

# ---- Response / Output ----
class OutUser(BaseModel):
    id: int = Field(..., alias="idUser")
    username: str = Field(..., alias="user")
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class RoleUser(BaseModel):
    name: str
    description: Optional[str] = None


# --- Auth / Tokens ---

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None  # seconds
class AuthResponse(BaseModel):
    user_data: OutUser = Field(..., alias="userData")
    token: Token = Field(...,alias="tokenUser")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True



