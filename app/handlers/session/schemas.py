import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ---- Request / Input ---- SESSION
class OpenSession(BaseModel):
    user_id: int = Field(..., alias="userId")
    client_id: Optional[int] = Field(None, alias="clientId")
    id_address: Optional[str] = Field(None, alias="ipAddress")
    user_agent: Optional[str] = Field(None, alias="userAgent")

    class Config:
        validate_by_name = True


class CloseSession(BaseModel):
    id: int = Field(..., alias="sessionId")

    class Config:
        validate_by_name = True


class RefreshSession(BaseModel):
    id: int = Field(..., alias="sessionId")
    user_id: int = Field(..., alias="userId")
    client_id: Optional[int] = Field(None, alias="clientId")
    access_token: Optional[str] = Field(None, alias="accessToken")
    refresh_token_id: Optional[int] = Field(None, alias="refreshTokenId")
    id_address: Optional[str] = Field(None, alias="ipAddress")
    user_agent: Optional[str] = Field(None, alias="userAgent")

    class Config:
        validate_by_name = True


class CheckSessionAccessToken(BaseModel):
    id: int = Field(..., alias="Id")
    user_id: int = Field(..., alias="UserId")
    access_token: str = Field(..., alias="AccessToken")
    id_address: str = Field(..., alias="ipAddress")
    user_agent: str = Field(..., alias="userAgent")


    class Config:
        validate_by_name = True


class CheckSessionRefreshToken(BaseModel):
    id: int = Field(..., alias="Id")
    user_id: int = Field(..., alias="UserId")
    refresh_token: str = Field(..., alias="refreshToken")
    ip_address: Optional[str] = Field(None, alias="ipAddress")
    user_agent: Optional[str] = Field(None, alias="userAgent")

# ---- Response / Output ---- SESSION
class OutSession(BaseModel):
    id: int = Field(..., alias="sessionId")
    user_id: int = Field(..., alias="userId")
    client_id: Optional[int] = Field(None, alias="clientId")
    access_token: Optional[str] = Field(None, alias="accessToken")
    refresh_token: str = Field(..., alias="refreshTokenId")
    is_active: Optional[bool] = Field(None, alias="isActive")
    logged_out_at: Optional[datetime.datetime] = Field(None, alias="loggedOutAt")
    created_at: Optional[datetime.datetime] = Field(None, alias="createdAt")
    last_used_at: Optional[datetime.datetime] = Field(None, alias="lastUserAt")

    class Config:
        validate_by_name = True
        from_attributes = True


# ---- Request / Input ---- RefreshToken

class CreateRefreshToken(BaseModel):
    session_id: int = Field(..., alias="sessionId")
    expires_at: Optional[datetime.datetime] = Field(None, alias="ExpiresAt")

    class Config:
        validate_by_name = True


class UpdateRefreshToken(BaseModel):
    id: int = Field(..., alias="Id")
    session_id: int = Field(..., alias="sessionId")
    revoked: Optional[bool] = Field(None, alias="Revoked")
    expires_at: Optional[datetime.datetime] = Field(None, alias="ExpiresAt")

    class Config:
        validate_by_name = True


# ---- Response / Output ---- RefreshToken

class OutRefreshToken(BaseModel):
    id: int = Field(..., alias="Id")
    session_id: int = Field(..., alias="sessionId")
    revoked: bool = Field(..., alias="Revoked")
    created_at: datetime.datetime = Field(..., alias="CreatedAt")
    expires_at: datetime.datetime = Field(..., alias="ExpiresAt")
    used_at: Optional[datetime.datetime] = Field(..., alias="UsedAt")
    token_hash: Optional[str] = Field(..., alias="TokenHash")

    class Config:
        validate_by_name = True


# ---- Request / Input ---- OauthClient


class CreateOauthClient(BaseModel):
    name: str = Field(..., alias="Name")
    client_id: str = Field(..., alias="ClientId")
    redirect_url: Optional[str] = Field(None, alias="RedirectUrl")
    grant_types: list[str] = Field(..., alias="GrantType")
    scopes: list[str] = Field(..., alias="Scopes")
    is_confidential: bool = Field(..., alias="IsConfidential")

    class Config:
        validate_by_name = True


class UpdateOauthClient(BaseModel):
    id: int = Field(..., alias="Id")
    name: Optional[str] = Field(None, alias="Name")
    client_id: Optional[str] = Field(None, alias="ClientId")
    redirect_url: Optional[str] = Field(None, alias="RedirectUrl")
    grant_types: Optional[list[str]] = Field(None, alias="GrantType")
    scopes: Optional[list[str]] = Field(None, alias="Scopes")
    is_confidential: Optional[bool] = Field(None, alias="IsConfidential")

    class Config:
        validate_by_name = True


class CheckOauthClient(BaseModel):
    id: int = Field(..., alias="Id")
    client_id: str = Field(..., alias="ClientId")
    grant_types: Optional[str] = Field(None, alias="GrantType")
    redirect_url: Optional[str] = Field(None, alias="RedirectUrl")
    scopes: Optional[list[str]] = Field(None, alias="Scopes")
    is_confidential: Optional[bool] = Field(None, alias="IsConfidential")

    class Config:
        validate_by_name = True


# ---- Response / Output ---- OauthClient


class OutOauthClient(BaseModel):
    name: str = Field(..., alias="Name")
    client_id: str = Field(..., alias="ClientId")
    client_secret: str = Field(..., alias="ClientSecret")
    redirect_url: Optional[str] = Field(None, alias="RedirectUrl")
    grant_types: list[str] = Field(..., alias="GrantType")
    scopes: list[str] = Field(..., alias="Scopes")
    is_confidential: bool = Field(..., alias="IsConfidential")
    created_at: datetime.datetime = Field(..., alias="CreatedAt")
    updated_at: datetime.datetime = Field(..., alias="UpdatedAt")

    class Config:
        validate_by_name = True
        from_attributes = True
