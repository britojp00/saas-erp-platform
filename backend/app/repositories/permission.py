from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.permission import Permission
from app.db.models.role_permission import RolePermission
from app.db.models.user_role import UserRole


class PermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_names_by_user(
        self,
        user_id: int,
        tenant_id: int,
    ) -> set[str]:
        stmt = (
            select(distinct(Permission.name))
            .join(
                RolePermission,
                (RolePermission.permission_id == Permission.id)
                & (RolePermission.tenant_id == Permission.tenant_id),
            )
            .join(
                UserRole,
                (UserRole.role_id == RolePermission.role_id)
                & (UserRole.tenant_id == RolePermission.tenant_id),
            )
            .where(
                UserRole.user_id == user_id,
                UserRole.tenant_id == tenant_id,
                Permission.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())
