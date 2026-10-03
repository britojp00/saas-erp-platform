from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.pedido import Pedido

SORT_FIELDS = {
    "numero_pedido": Pedido.numero_pedido,
    "status": Pedido.status,
    "total_amount": Pedido.total_amount,
    "cliente_id": Pedido.cliente_id,
    "created_at": Pedido.created_at,
    "updated_at": Pedido.updated_at,
}


class PedidoRepository:
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
        status: str | None = None,
        cliente_id: int | None = None,
    ) -> tuple[list[Pedido], int]:
        base_stmt = select(Pedido).where(
            Pedido.empresa_id == empresa_id,
            Pedido.deleted_at.is_(None),
        )
        if search:
            base_stmt = base_stmt.where(
                Pedido.numero_pedido.cast(str).ilike(f"%{search}%")
                | Pedido.notes.ilike(f"%{search}%")
            )
        if status is not None:
            base_stmt = base_stmt.where(Pedido.status == status)
        if cliente_id is not None:
            base_stmt = base_stmt.where(Pedido.cliente_id == cliente_id)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        sort_column = SORT_FIELDS.get(sort, Pedido.created_at)
        if order == "asc":
            base_stmt = base_stmt.order_by(sort_column.asc(), Pedido.id.asc())
        else:
            base_stmt = base_stmt.order_by(sort_column.desc(), Pedido.id.desc())

        base_stmt = base_stmt.offset(offset).limit(limit)
        result = await self.session.execute(base_stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_by_id(
        self,
        empresa_id: int,
        pedido_id: int,
    ) -> Pedido | None:
        stmt = select(Pedido).where(
            Pedido.id == pedido_id,
            Pedido.empresa_id == empresa_id,
            Pedido.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_update(
        self,
        empresa_id: int,
        pedido_id: int,
    ) -> Pedido | None:
        stmt = (
            select(Pedido)
            .where(
                Pedido.id == pedido_id,
                Pedido.empresa_id == empresa_id,
                Pedido.deleted_at.is_(None),
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def proximo_numero_pedido(
        self,
        empresa_id: int,
    ) -> int:
        from sqlalchemy import text

        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:eid))"),
            {"eid": str(empresa_id)},
        )

        stmt = select(func.max(Pedido.numero_pedido)).where(
            Pedido.empresa_id == empresa_id,
        )
        result = await self.session.execute(stmt)
        max_num = result.scalar_one()

        if max_num is None:
            return 1
        return int(max_num) + 1

    async def create(self, pedido: Pedido) -> Pedido:
        self.session.add(pedido)
        await self.session.flush()
        return pedido

    async def update(self, pedido: Pedido) -> Pedido:
        await self.session.flush()
        await self.session.refresh(pedido)
        return pedido
