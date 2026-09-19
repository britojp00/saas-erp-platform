from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_permissions
from app.core.exceptions import AuthenticationError
from app.db.database import get_db_session
from app.repositories.role import RoleRepository
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services.auth import AuthService
from app.services.authorization import AuthorizationService

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
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserResponse:
    auth_service = AuthorizationService(db)
    roles = await auth_service.get_user_roles(current_user.id, current_user.tenant_id)
    permissions = await auth_service.get_user_permissions(
        current_user.id, current_user.tenant_id
    )
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        tenant_id=current_user.tenant_id,
        created_at=current_user.created_at,
        roles=roles,
        permissions=sorted(permissions),
    )


@router.get(
    "/roles",
    dependencies=[
        Depends(require_permissions("role.read")),
    ],
)
async def list_roles(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[dict[str, str]]:
    role_repo = RoleRepository(db)
    roles = await role_repo.list_by_tenant(current_user.tenant_id)
    return [{"id": str(r.id), "name": r.name} for r in roles]
