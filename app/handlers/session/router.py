from fastapi import APIRouter,HTTPException
from app.handlers.auth.schemas import LogInUser, UserCreate, LogOutUser, AuthResponse,RoleUser
from app.handlers.session.dependencies import SessionServiceDep
from app.handlers.session.schemas import OpenSession, CloseSession, OutSession, CheckSessionAccessToken

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

@router.post("/refresh_token",response_model=OutSession)
async def validate_session(session_service: SessionServiceDep,id: int, user_id: int, access_token: str, ip: str, user_agent: str):

    session_data = CheckSessionAccessToken(
        id=id,
        user_id=user_id,
        access_token=access_token,
        id_address=ip,
        user_agent=user_agent,
    )

    return await session_service.validate_refresh_token_session(session_data)