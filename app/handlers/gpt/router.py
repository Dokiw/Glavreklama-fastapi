
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends,  Request


from app.handlers.gpt.dependencies import gptServiceDep
from app.handlers.gpt.schemas import GPTCreate, OutGPTkey
from app.handlers.session.schemas import CheckSessionAccessToken
from app.method.get_token import get_token

router = APIRouter(prefix="/gpt", tags=["gpt"])


@router.get("/")
async def hub():
    """
    Используется для возврата 200-го статуса на главной странице FastApi()
    :return:
    """
    return HTTPException(200, 'Status - True')


@router.post("/create_gtp_prompt", response_model=dict)
async def create_gtp_prompt(
        data: GPTCreate,
        request: Request,
        gpt_service: gptServiceDep,
        image_url: Optional[str] = None,
        access_token: str = Depends(get_token)
):
    """
    Создание gpt-промпта, принимает данные для генерации и id пользователя, собирает ip и user-agent,
    формирует данные проверки сессии, передаёт их в сервис gpt и возвращает результат операции
    :param data:
    :param request:
    :param gpt_service:
    :param image_url:
    :param access_token:
    :return:
    """
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=data.user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token
    )

    return await gpt_service.create_gtp_promt(model=data.model, system_prompt=data.system_prompt, image_url=image_url,
                                              check_data=csat)


@router.get("/get_property_key", response_model=OutGPTkey)
async def create_gtp_prompt(
        oauth_client: str,
        user_id: int,
        request: Request,
        gpt_service: gptServiceDep,
        access_token: str = Depends(get_token)
):
    """
    Получение ключа gpt, принимает oauth_client и id пользователя, собирает ip и user-agent,
    формирует данные проверки сессии, передаёт их в сервис gpt и возвращает результат операции.
    :param oauth_client:
    :param user_id:
    :param request:
    :param gpt_service:
    :param access_token:
    :return:
    """
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token
    )

    return await gpt_service.get_property_key(oauth_client=oauth_client, check_data=csat)
