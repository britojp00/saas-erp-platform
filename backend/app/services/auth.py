from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    verify_password,
)
from app.db.models.user import User
from app.repositories.empresa import EmpresaRepository
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse
from app.services.audit_log import AuditLogService


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.empresa_repo = EmpresaRepository(session)
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
                    empresa_id=candidates[0].empresa_id,
                    user_id=candidates[0].id,
                    action="LOGIN_FALHA",
                    entity_type="user",
                    entity_id=candidates[0].id,
                    description="Senha inválida",
                )
            raise AuthenticationError("Credenciais inválidas")

        user = matched_users[0]

        if not user.is_active:
            await self.audit_service.log(
                empresa_id=user.empresa_id,
                user_id=user.id,
                action="LOGIN_FALHA",
                entity_type="user",
                entity_id=user.id,
                description="Usuário inativo",
            )
            raise AuthenticationError("Credenciais inválidas")

        if user.deleted_at is not None:
            await self.audit_service.log(
                empresa_id=user.empresa_id,
                user_id=user.id,
                action="LOGIN_FALHA",
                entity_type="user",
                entity_id=user.id,
                description="Usuário excluído",
            )
            raise AuthenticationError("Credenciais inválidas")

        empresa = await self.empresa_repo.get_by_id(user.empresa_id)

        if empresa is None or not empresa.is_active:
            await self.audit_service.log(
                empresa_id=user.empresa_id,
                user_id=user.id,
                action="LOGIN_FALHA",
                entity_type="user",
                entity_id=user.id,
                description="Empresa inativa",
            )
            raise AuthenticationError("Credenciais inválidas")

        token = create_access_token(
            data={
                "sub": str(user.id),
                "empresa_id": str(user.empresa_id),
            }
        )

        await self.audit_service.log(
            empresa_id=user.empresa_id,
            user_id=user.id,
            action="LOGIN_SUCESSO",
            entity_type="user",
            entity_id=user.id,
        )

        return TokenResponse(access_token=token)

    async def get_current_user(
        self,
        user_id: int,
        empresa_id: int,
    ) -> User:
        user = await self.user_repo.get_by_id_and_empresa(user_id, empresa_id)

        if user is None:
            raise AuthenticationError("Credenciais inválidas")

        if not user.is_active:
            raise AuthenticationError("Credenciais inválidas")

        if user.deleted_at is not None:
            raise AuthenticationError("Credenciais inválidas")

        empresa = await self.empresa_repo.get_by_id(empresa_id)

        if empresa is None or not empresa.is_active:
            raise AuthenticationError("Credenciais inválidas")

        return user
