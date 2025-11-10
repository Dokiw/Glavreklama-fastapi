from fastapi import APIRouter, HTTPException, Depends, Header, Request
from app.handlers.auth.schemas import LogInUser, UserCreate, LogOutUser, AuthResponse,RoleUser
from app.handlers.session.dependencies import SessionServiceDep, OauthClientServiceDep
from app.handlers.session.schemas import OpenSession, CloseSession, OutSession, CheckSessionAccessToken, \
    CheckSessionRefreshToken, OutOauthClient, CheckOauthClient

router = APIRouter(prefix="/session", tags=["session"])

@router.get("/")
async def hub():
    return HTTPException(200,'Status - True')


# @router.post("/open",response_model=OpenSession)
# async def open_session(session_data: OpenSession,session_service: SessionServiceDep):
#     return await session_service.open_session(session_data)
#
# @router.post("/close",response_model=CloseSession)
# async def close_session(session_close: CloseSession, session_service: SessionServiceDep):
#     return await session_service.close_session(session_close)


# todo - заготовка под новый сервер и получение информации.
# @router.post("/refresh_token",response_model=OutOauthClient)
# async def valid_server(session_service: SessionServiceDep, oauth_client: str, oauth_client_secret: str):
#     return None


@router.post("/refresh_token",response_model=OutSession)
async def validate_session(session_service: SessionServiceDep, user_id: int,
                           refresh_token: str, oauth_client: str, request: Request):
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