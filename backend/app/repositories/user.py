from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_by_email(self, email: str) -> list[User]:
        stmt = select(User).where(
            User.email == email,
            User.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_and_empresa(
        self,
        user_id: int,
        empresa_id: int,
    ) -> User | None:
        stmt = select(User).where(
            User.id == user_id,
            User.empresa_id == empresa_id,
            User.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
