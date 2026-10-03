from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.reserva_estoque import ReservaEstoque, StatusReserva


class ReservaEstoqueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, reserva: ReservaEstoque) -> ReservaEstoque:
        self.session.add(reserva)
        await self.session.flush()
        return reserva

    async def get_by_id(
        self,
        empresa_id: int,
        reserva_id: int,
    ) -> ReservaEstoque | None:
        stmt = select(ReservaEstoque).where(
            ReservaEstoque.empresa_id == empresa_id,
            ReservaEstoque.id == reserva_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        empresa_id: int,
        *,
        offset: int,
        limit: int,
        produto_id: int | None = None,
    ) -> tuple[list[ReservaEstoque], int]:
        base_stmt = select(ReservaEstoque).where(
            ReservaEstoque.empresa_id == empresa_id,
        )
        if produto_id is not None:
            base_stmt = base_stmt.where(ReservaEstoque.produto_id == produto_id)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        base_stmt = base_stmt.order_by(
            ReservaEstoque.reserved_at.desc(),
            ReservaEstoque.id.desc(),
        )
        base_stmt = base_stmt.offset(offset).limit(limit)
        result = await self.session.execute(base_stmt)
        items = list(result.scalars().all())

        return items, total

    async def list_active_by_reference(
        self,
        empresa_id: int,
        reference: str,
    ) -> list[ReservaEstoque]:
        stmt = (
            select(ReservaEstoque)
            .where(
                ReservaEstoque.empresa_id == empresa_id,
                ReservaEstoque.reference == reference,
                ReservaEstoque.status == StatusReserva.ATIVA,
            )
            .order_by(ReservaEstoque.produto_id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def exists_by_idempotency_key(
        self,
        empresa_id: int,
        idempotency_key: str,
    ) -> bool:
        stmt = select(ReservaEstoque).where(
            ReservaEstoque.empresa_id == empresa_id,
            ReservaEstoque.idempotency_key == idempotency_key,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def update(self, reserva: ReservaEstoque) -> ReservaEstoque:
        await self.session.flush()
        await self.session.refresh(reserva)
        return reserva
