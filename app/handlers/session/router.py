from fastapi import APIRouter, HTTPException, Depends, Header, Request, Body
from app.handlers.auth.schemas import LogInUser, UserCreate, LogOutUser, AuthResponse,RoleUser
from app.handlers.session.dependencies import SessionServiceDep, OauthClientServiceDep
from app.handlers.session.schemas import OpenSession, CloseSession, OutSession, CheckSessionAccessToken, \
    CheckSessionRefreshToken, OutOauthClient, CheckOauthClient
from app.method.get_token import get_token

router = APIRouter(prefix="/session", tags=["session"])

@router.get("/")
async def hub():
    """
    Используется для возврата 200-го статуса на главной странице FastApi()
    :return:
    """
    return HTTPException(200,'Status - True')


# @router.post("/open",response_model=OpenSession)
# async def open_session(session_data: OpenSession,session_service: SessionServiceDep):
#     return await session_service.open_session(session_data)
#
# @router.post("/close",response_model=CloseSession)
# async def close_session(session_close: CloseSession, session_service: SessionServiceDep):
#     return await session_service.close_session(session_close)


# todo - заготовка под новый сервер и получение информации.
@router.post("/access_token", response_model=OutSession)
async def valid_server_session(
        session_service: SessionServiceDep,
        csat: CheckSessionAccessToken = Body(...),
):

    return await session_service.validate_access_token_session(csat)


@router.post("/refresh_token",response_model=OutSession)
async def validate_session(session_service: SessionServiceDep, user_id: int,
                           refresh_token: str, oauth_client: str, request: Request):
    """
    Обновление токена, принимает id пользователя, собирает ip и user-agent,
    формирует данные проверки сессии, передаёт их вместе с параметрами платежа в сервис
    и возвращает результат операции
    :param session_service:
    :param user_id:
    :param refresh_token:
    :param oauth_client:
    :param request:
    :return:
    """
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    session_data = CheckSessionRefreshToken(
        user_id=user_id,
        refresh_token=refresh_token,
        id_address=ip,
        user_agent=user_agent,
        oauth_client=oauth_client,
    )
    return await session_service.validate_refresh_token_session(session_data)