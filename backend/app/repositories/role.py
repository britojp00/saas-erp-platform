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
        empresa_id: int,
    ) -> list[str]:
        stmt = (
            select(distinct(Role.name))
            .join(
                UserRole,
                (UserRole.role_id == Role.id)
                & (UserRole.empresa_id == Role.empresa_id),
            )
            .where(
                UserRole.user_id == user_id,
                UserRole.empresa_id == empresa_id,
                Role.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_empresa(
        self,
        empresa_id: int,
    ) -> list[Role]:
        stmt = select(Role).where(
            Role.empresa_id == empresa_id,
            Role.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
