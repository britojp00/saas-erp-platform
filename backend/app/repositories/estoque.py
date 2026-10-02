from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.estoque import Estoque


class EstoqueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_produto_id(
        self,
        tenant_id: int,
        produto_id: int,
    ) -> Estoque | None:
        stmt = select(Estoque).where(
            Estoque.tenant_id == tenant_id,
            Estoque.produto_id == produto_id,
            Estoque.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_update(
        self,
        tenant_id: int,
        produto_id: int,
    ) -> Estoque | None:
        stmt = (
            select(Estoque)
            .where(
                Estoque.tenant_id == tenant_id,
                Estoque.produto_id == produto_id,
                Estoque.deleted_at.is_(None),
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        tenant_id: int,
        *,
        offset: int,
        limit: int,
        produto_id: int | None = None,
    ) -> tuple[list[Estoque], int]:
        base_stmt = select(Estoque).where(
            Estoque.tenant_id == tenant_id,
            Estoque.deleted_at.is_(None),
        )
        if produto_id is not None:
            base_stmt = base_stmt.where(Estoque.produto_id == produto_id)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        base_stmt = base_stmt.order_by(Estoque.created_at.desc(), Estoque.id.desc())
        base_stmt = base_stmt.offset(offset).limit(limit)
        result = await self.session.execute(base_stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_or_create(
        self,
        tenant_id: int,
        produto_id: int,
    ) -> Estoque:
        estoque = await self.get_by_produto_id(tenant_id, produto_id)
        if estoque is None:
            estoque = Estoque(
                tenant_id=tenant_id,
                produto_id=produto_id,
            )
            self.session.add(estoque)
            await self.session.flush()
        return estoque
