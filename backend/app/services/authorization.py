from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.permission import PermissionRepository
from app.repositories.role import RoleRepository


class AuthorizationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.permission_repo = PermissionRepository(session)
        self.role_repo = RoleRepository(session)

    async def get_user_permissions(
        self,
        user_id: int,
        tenant_id: int,
    ) -> set[str]:
        return await self.permission_repo.get_names_by_user(user_id, tenant_id)

    async def get_user_roles(
        self,
        user_id: int,
        tenant_id: int,
    ) -> list[str]:
        return await self.role_repo.get_names_by_user(user_id, tenant_id)

    async def has_all_permissions(
        self,
        user_id: int,
        tenant_id: int,
        required: set[str],
    ) -> bool:
        permissions = await self.get_user_permissions(user_id, tenant_id)
        return required.issubset(permissions)
