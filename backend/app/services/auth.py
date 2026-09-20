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
from app.services.audit_log import AuditLogService


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.tenant_repo = TenantRepository(session)
        self.audit_service = AuditLogService(session)

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
            if candidates:
                await self.audit_service.log(
                    tenant_id=candidates[0].tenant_id,
                    user_id=candidates[0].id,
                    action="LOGIN_FAILURE",
                    entity_type="user",
                    entity_id=candidates[0].id,
                    description="Invalid password",
                )
            raise AuthenticationError("Credenciais inválidas")

        user = matched_users[0]

        if not user.is_active:
            await self.audit_service.log(
                tenant_id=user.tenant_id,
                user_id=user.id,
                action="LOGIN_FAILURE",
                entity_type="user",
                entity_id=user.id,
                description="Inactive user",
            )
            raise AuthenticationError("Credenciais inválidas")

        if user.deleted_at is not None:
            await self.audit_service.log(
                tenant_id=user.tenant_id,
                user_id=user.id,
                action="LOGIN_FAILURE",
                entity_type="user",
                entity_id=user.id,
                description="Deleted user",
            )
            raise AuthenticationError("Credenciais inválidas")

        tenant = await self.tenant_repo.get_by_id(user.tenant_id)

        if tenant is None or not tenant.is_active:
            await self.audit_service.log(
                tenant_id=user.tenant_id,
                user_id=user.id,
                action="LOGIN_FAILURE",
                entity_type="user",
                entity_id=user.id,
                description="Inactive tenant",
            )
            raise AuthenticationError("Credenciais inválidas")

        token = create_access_token(
            data={
                "sub": str(user.id),
                "tenant_id": str(user.tenant_id),
            }
        )

        await self.audit_service.log(
            tenant_id=user.tenant_id,
            user_id=user.id,
            action="LOGIN_SUCCESS",
            entity_type="user",
            entity_id=user.id,
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
