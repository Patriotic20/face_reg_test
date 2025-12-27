from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from .services import AuthService
from .schemas import (
    UserCreate, 
    UserLogin, 
    RefreshRequest, 
    UpdatePassword
)

from models.user import User
from core.db_helper import db_helper
from core.utils.dependencies import require_permission


router = APIRouter(
    tags=["Auth"],
    prefix="/auth"
)


def get_auth_servies(session: AsyncSession = Depends(db_helper.session_getter)):
    return AuthService(session)

@router.post("/users")
async def register_user(
    user_credentials: UserCreate,
    service: AuthService = Depends(get_auth_servies)
):
    return await service.register_user(credentials=user_credentials)

@router.post("/login")
async def login_user(
    user_credentials: UserLogin,
    service: AuthService = Depends(get_auth_servies)
):
    return await service.login_user(credentials=user_credentials)

@router.post("/token/refresh")
async def refresh_token(
    user_credentials: RefreshRequest,
    service: AuthService = Depends(get_auth_servies)
):
    return await service.refresh_token(credentials=user_credentials)

@router.get("/me")
async def get_current_user(
    current_user: User = Depends(require_permission("auth:me"))
):
    return current_user

@router.put("/users/me/password")
async def change_password(
    password_data: UpdatePassword,
    service: AuthService = Depends(get_auth_servies),
    current_user: User = Depends(require_permission("auth:password"))
):
    return await service.change_password(credentials=password_data, current_user=current_user)
