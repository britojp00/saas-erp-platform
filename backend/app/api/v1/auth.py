from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser
from app.core.exceptions import AuthenticationError
from app.db.database import get_db_session
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def get_auth_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthService:
    return AuthService(db)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        return await service.authenticate(data.email, data.password)
    except AuthenticationError:
        raise AuthenticationError("Credenciais inválidas")


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: CurrentUser,
) -> UserResponse:
    return current_user
