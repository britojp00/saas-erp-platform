from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.movimentacao_estoque import MovimentacaoEstoque


class MovimentacaoEstoqueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, movimentacao: MovimentacaoEstoque) -> MovimentacaoEstoque:
        self.session.add(movimentacao)
        await self.session.flush()
        return movimentacao

    async def list(
        self,
        tenant_id: int,
        *,
        offset: int,
        limit: int,
        produto_id: int | None = None,
    ) -> tuple[list[MovimentacaoEstoque], int]:
        base_stmt = select(MovimentacaoEstoque).where(
            MovimentacaoEstoque.tenant_id == tenant_id,
        )
        if produto_id is not None:
            base_stmt = base_stmt.where(MovimentacaoEstoque.produto_id == produto_id)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        base_stmt = base_stmt.order_by(
            MovimentacaoEstoque.performed_at.desc(), MovimentacaoEstoque.id.desc()
        )
        base_stmt = base_stmt.offset(offset).limit(limit)
        result = await self.session.execute(base_stmt)
        items = list(result.scalars().all())

        return items, total

    async def exists_by_idempotency_key(
        self,
        tenant_id: int,
        idempotency_key: str,
    ) -> bool:
        stmt = select(MovimentacaoEstoque).where(
            MovimentacaoEstoque.tenant_id == tenant_id,
            MovimentacaoEstoque.idempotency_key == idempotency_key,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
