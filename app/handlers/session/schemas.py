import datetime as dt
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ---- Request / Input ---- SESSION
class OpenSession(BaseModel):
    user_id: int = Field(..., alias="userId")
    id_address: Optional[str] = Field(None, alias="ipAddress")
    user_agent: Optional[str] = Field(None, alias="userAgent")

    client_id: Optional[str] = Field(None, alias="clientId")
    client_secret: Optional[str] = Field(None, alias="clientSecret")

    class Config:
        validate_by_name = True


class OpenSessionRepo(BaseModel):
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
    refresh_token: Optional[str] = Field(None, alias="refreshToken")
    ip_address: Optional[str] = Field(None, alias="ipAddress")
    user_agent: Optional[str] = Field(None, alias="userAgent")

    class Config:
        validate_by_name = True


class CheckSessionAccessToken(BaseModel):
    user_id: int = Field(..., alias="UserId")
    access_token: str = Field(..., alias="AccessToken")
    ip_address: str = Field(..., alias="ipAddress")
    user_agent: str = Field(..., alias="userAgent")

    class Config:
        validate_by_name = True


class CheckSessionRefreshToken(BaseModel):
    user_id: int = Field(..., alias="UserId")
    refresh_token: str = Field(..., alias="refreshToken")
    ip_address: Optional[str] = Field(None, alias="ipAddress")
    user_agent: Optional[str] = Field(None, alias="userAgent")
    oauth_client: str = Field(..., alias="oauth_Client")

    class Config:
        validate_by_name = True


class LogoutSession(BaseModel):
    user_id: int = Field(..., alias="UserId")
    access_token: str = Field(..., alias="AccessToken")
    id_address: str = Field(..., alias="ipAddress")
    user_agent: str = Field(..., alias="userAgent")

    class Config:
        validate_by_name = True


# ---- Response / Output ---- SESSION
class OutSession(BaseModel):
    id: int = Field(..., alias="sessionId")
    user_id: int = Field(..., alias="userId")
    client_id: Optional[int] = Field(None, alias="clientId")
    access_token: Optional[str] = Field(None, alias="accessToken")
    refresh_token: Optional[str] = Field(None, alias="refreshToken")
    is_active: Optional[bool] = Field(None, alias="isActive")
    logged_out_at: Optional[dt.datetime] = Field(None, alias="loggedOutAt")
    created_at: Optional[dt.datetime] = Field(None, alias="createdAt")
    last_used_at: Optional[dt.datetime] = Field(None, alias="lastUserAt")
    ip_address: Optional[str] = Field(None, alias="IpAddress")
    user_agent: Optional[str] = Field(None, alias="UserAgent")

    class Config:
        validate_by_name = True
        from_attributes = True


# ---- Request / Input ---- RefreshToken

class CreateRefreshToken(BaseModel):
    session_id: int = Field(..., alias="sessionId")
    expires_at: Optional[dt.datetime] = Field(None, alias="ExpiresAt")

    model_config = {
        "populate_by_name": True
    }


class UpdateRefreshToken(BaseModel):
    id: int = Field(..., alias="Id")
    session_id: int = Field(..., alias="SessionId")
    revoked: Optional[bool] = Field(None, alias="Revoked")
    expires_at: Optional[dt.datetime] = Field(None, alias="ExpiresAt")

    class Config:
        validate_by_name = True


# ---- Response / Output ---- RefreshToken

class OutRefreshToken(BaseModel):
    id: int = Field(..., alias="Id")
    session_id: int = Field(..., alias="sessionId")
    revoked: bool = Field(..., alias="Revoked")
    created_at: dt.datetime = Field(..., alias="CreatedAt")
    expires_at: dt.datetime = Field(..., alias="ExpiresAt")
    used_at: Optional[dt.datetime] = Field(..., alias="UsedAt")
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
    revoked: Optional[bool] = Field(None, alias="Revoked")

    class Config:
        validate_by_name = True


class CheckOauthClient(BaseModel):
    client_id: str = Field(..., alias="ClientId")
    client_secret: Optional[str] = Field(None, alias="ClientSecret")

    class Config:
        validate_by_name = True


# ---- Response / Output ---- OauthClient


class OutOauthClient(BaseModel):
    id: int = Field(..., alias="id")
    name: str = Field(..., alias="Name")
    client_id: str = Field(..., alias="ClientId")
    client_secret: Optional[str] = Field(None, alias="ClientSecret")
    client_bot_token: Optional[str] = Field(None, alias="ClientSecret")
    redirect_url: Optional[str] = Field(None, alias="RedirectUrl")
    grant_types: Optional[list[str]] = Field(None, alias="GrantType")
    scopes: Optional[list[str]] = Field(None, alias="Scopes")
    is_confidential: bool = Field(..., alias="IsConfidential")
    created_at: Optional[dt.datetime] = Field(None, alias="CreatedAt")
    updated_at: Optional[dt.datetime] = Field(None, alias="UpdatedAt")
    revoked: bool = Field(..., alias="Revoked")

    class Config:
        validate_by_name = True
        from_attributes = True
