import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Header, Request, Body, Form


from app.handlers.gpt.dependencies import gptServiceDep
from app.handlers.session.schemas import CheckSessionAccessToken
from app.method.get_token import get_token

router = APIRouter(prefix="/gpt", tags=["gpt"])


@router.get("/")
async def hub():
    return HTTPException(200, 'Status - True')


@router.post("/create_gtp_promt", response_model=dict)
async def create_gtp_promt(
        model: str,
        system_prompt: str,
        user_id: int,
        request: Request,
        gpt_service: gptServiceDep,
        image_url: Optional[str] = None,
        access_token: str = Depends(get_token)
):
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token
    )

    return await gpt_service.create_gtp_promt(model=model, system_prompt=system_prompt, image_url=image_url,
                                              check_data=csat)
