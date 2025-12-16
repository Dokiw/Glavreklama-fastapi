from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

from app.handlers.providers.schemas import ProviderOut, ProviderLoginRequest


# ---- Request / Input ----

class GPTCreate(BaseModel):
    model: str = Field(..., alias="Model")
    system_prompt: str = Field(..., alias="SystemPrompt")
    user_id: int = Field(..., alias="UserId")

    class Config:
        validate_by_name = True


# ---- Response / Output ----

class OutGPTkey(BaseModel):
    user_id: int = Field(..., alias="UserId")
    data: str = Field(..., alias="Data")


    class Config:
        validate_by_name = True

