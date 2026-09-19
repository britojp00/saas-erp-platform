from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.role import Role
from app.db.models.user_role import UserRole


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_names_by_user(
        self,
        user_id: int,
        tenant_id: int,
    ) -> list[str]:
        stmt = (
            select(distinct(Role.name))
            .join(
                UserRole,
                (UserRole.role_id == Role.id) & (UserRole.tenant_id == Role.tenant_id),
            )
            .where(
                UserRole.user_id == user_id,
                UserRole.tenant_id == tenant_id,
                Role.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_tenant(
        self,
        tenant_id: int,
    ) -> list[Role]:
        stmt = select(Role).where(
            Role.tenant_id == tenant_id,
            Role.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
