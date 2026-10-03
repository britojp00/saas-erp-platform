from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.empresa import Empresa


class EmpresaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, empresa_id: int) -> Empresa | None:
        stmt = select(Empresa).where(
            Empresa.id == empresa_id,
            Empresa.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
