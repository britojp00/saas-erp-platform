from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    verify_password,
)
from app.db.models.user import User
from app.repositories.tenant import TenantRepository
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.tenant_repo = TenantRepository(session)

    async def authenticate(
        self,
        email: str,
        password: str,
    ) -> TokenResponse:
        normalized_email = email.strip().lower()

        candidates = await self.user_repo.get_active_by_email(normalized_email)

        if not candidates:
            raise AuthenticationError("Credenciais inválidas")

        matched_users: list[User] = []
        for candidate in candidates:
            if verify_password(password, candidate.password_hash):
                matched_users.append(candidate)

        if len(matched_users) != 1:
            raise AuthenticationError("Credenciais inválidas")

        user = matched_users[0]

        if not user.is_active:
            raise AuthenticationError("Credenciais inválidas")

        if user.deleted_at is not None:
            raise AuthenticationError("Credenciais inválidas")

        tenant = await self.tenant_repo.get_by_id(user.tenant_id)

        if tenant is None or not tenant.is_active:
            raise AuthenticationError("Credenciais inválidas")

        token = create_access_token(
            data={
                "sub": str(user.id),
                "tenant_id": str(user.tenant_id),
            }
        )

        return TokenResponse(access_token=token)

    async def get_current_user(
        self,
        user_id: int,
        tenant_id: int,
    ) -> User:
        user = await self.user_repo.get_by_id_and_tenant(user_id, tenant_id)

        if user is None:
            raise AuthenticationError("Credenciais inválidas")

        if not user.is_active:
            raise AuthenticationError("Credenciais inválidas")

        if user.deleted_at is not None:
            raise AuthenticationError("Credenciais inválidas")

        tenant = await self.tenant_repo.get_by_id(tenant_id)

        if tenant is None or not tenant.is_active:
            raise AuthenticationError("Credenciais inválidas")

        return user
