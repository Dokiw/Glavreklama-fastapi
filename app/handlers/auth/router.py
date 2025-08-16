from fastapi import APIRouter,HTTPException

from app.handlers.auth.schemas import LogInUser, UserCreate, LogOutUser, AuthResponse,RoleUser
from app.handlers.auth.service import SqlAlchemyAuth
from app.handlers.auth.crud import UserRepository,RoleRepository
from app.handlers.auth.dependencies import AuthServiceDep

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/")
async def hub():
    return HTTPException(200,'Status - True')

@router.post("/login",response_model=AuthResponse)
async def login(log_in_user: LogInUser,auth_service: AuthServiceDep):
    return await auth_service.login(log_in_user)
@router.post("/register",response_model=AuthResponse)
async def register(user_create: UserCreate,auth_service: AuthServiceDep):
    return await auth_service.register(user_create)

@router.post("/role",response_model=RoleUser)
async def indetificate(user_id: int,auth_service: AuthServiceDep):
    return await auth_service.identification(user_id)

@router.post("/logout")
async def logout(log_out_user: LogOutUser):
    return None