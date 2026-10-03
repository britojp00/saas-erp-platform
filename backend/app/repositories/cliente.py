from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cliente import Cliente

SORT_FIELDS = {
    "id": Cliente.id,
    "name": Cliente.name,
    "created_at": Cliente.created_at,
}


class ClienteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        empresa_id: int,
        *,
        offset: int,
        limit: int,
        search: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[Cliente], int]:
        base_stmt = select(Cliente).where(
            Cliente.empresa_id == empresa_id,
            Cliente.deleted_at.is_(None),
        )
        if search:
            base_stmt = base_stmt.where(Cliente.name.ilike(f"%{search}%"))

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        sort_column = SORT_FIELDS.get(sort, Cliente.created_at)
        if order == "asc":
            base_stmt = base_stmt.order_by(sort_column.asc(), Cliente.id.asc())
        else:
            base_stmt = base_stmt.order_by(sort_column.desc(), Cliente.id.desc())

        base_stmt = base_stmt.offset(offset).limit(limit)
        result = await self.session.execute(base_stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_by_id(
        self,
        cliente_id: int,
        empresa_id: int,
    ) -> Cliente | None:
        stmt = select(Cliente).where(
            Cliente.id == cliente_id,
            Cliente.empresa_id == empresa_id,
            Cliente.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_document(
        self,
        empresa_id: int,
        document: str,
        exclude_id: int | None = None,
    ) -> bool:
        stmt = select(Cliente).where(
            Cliente.empresa_id == empresa_id,
            Cliente.document == document,
        )
        if exclude_id is not None:
            stmt = stmt.where(Cliente.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, cliente: Cliente) -> Cliente:
        self.session.add(cliente)
        await self.session.flush()
        return cliente

    async def update(self, cliente: Cliente) -> Cliente:
        await self.session.flush()
        await self.session.refresh(cliente)
        return cliente

    async def soft_delete(self, cliente: Cliente) -> None:
        cliente.deleted_at = datetime.now(UTC)
        await self.session.flush()
