from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_auth_uc, get_current_user_id
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserPublic
from app.usecases.auth import AuthUseCase

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=201,
    summary="Register a new user",
)
async def register(
    data: RegisterRequest,
    auth_uc: AuthUseCase = Depends(get_auth_uc),
) -> UserPublic:
    return await auth_uc.register(data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT",
)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    auth_uc: AuthUseCase = Depends(get_auth_uc),
) -> TokenResponse:
    return await auth_uc.login(email=form.username, password=form.password)


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get current user profile",
)
async def me(
    user_id: int = Depends(get_current_user_id),
    auth_uc: AuthUseCase = Depends(get_auth_uc),
) -> UserPublic:
    return await auth_uc.get_me(user_id=user_id)
