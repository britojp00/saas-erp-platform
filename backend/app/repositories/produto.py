from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.categoria import Categoria
from app.db.models.estoque import Estoque
from app.db.models.pedido_item import PedidoItem
from app.db.models.produto import Produto

SORT_FIELDS = {
    "name": Produto.name,
    "sku": Produto.sku,
    "price": Produto.price,
    "is_active": Produto.is_active,
    "created_at": Produto.created_at,
}


class ProdutoRepository:
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
        categoria_id: int | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Produto], int]:
        base_stmt = select(Produto).where(
            Produto.empresa_id == empresa_id,
            Produto.deleted_at.is_(None),
        )
        if search:
            base_stmt = base_stmt.where(
                Produto.name.ilike(f"%{search}%") | Produto.sku.ilike(f"%{search}%")
            )
        if categoria_id is not None:
            base_stmt = base_stmt.where(Produto.categoria_id == categoria_id)
        if is_active is not None:
            base_stmt = base_stmt.where(Produto.is_active == is_active)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        sort_column = SORT_FIELDS.get(sort, Produto.created_at)
        if order == "asc":
            base_stmt = base_stmt.order_by(sort_column.asc(), Produto.id.asc())
        else:
            base_stmt = base_stmt.order_by(sort_column.desc(), Produto.id.desc())

        base_stmt = base_stmt.offset(offset).limit(limit)
        result = await self.session.execute(base_stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_by_id(
        self,
        produto_id: int,
        empresa_id: int,
    ) -> Produto | None:
        stmt = select(Produto).where(
            Produto.id == produto_id,
            Produto.empresa_id == empresa_id,
            Produto.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_categoria_by_id(
        self,
        categoria_id: int,
        empresa_id: int,
    ) -> Categoria | None:
        stmt = select(Categoria).where(
            Categoria.id == categoria_id,
            Categoria.empresa_id == empresa_id,
            Categoria.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_sku(
        self,
        empresa_id: int,
        sku: str,
        exclude_id: int | None = None,
    ) -> bool:
        stmt = select(Produto).where(
            Produto.empresa_id == empresa_id,
            Produto.sku == sku,
        )
        if exclude_id is not None:
            stmt = stmt.where(Produto.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def tem_estoque(
        self,
        empresa_id: int,
        produto_id: int,
    ) -> bool:
        stmt = (
            select(Estoque)
            .where(
                Estoque.empresa_id == empresa_id,
                Estoque.produto_id == produto_id,
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def tem_itens_pedido(
        self,
        empresa_id: int,
        produto_id: int,
    ) -> bool:
        stmt = (
            select(PedidoItem)
            .where(
                PedidoItem.empresa_id == empresa_id,
                PedidoItem.produto_id == produto_id,
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, produto: Produto) -> Produto:
        self.session.add(produto)
        await self.session.flush()
        return produto

    async def update(self, produto: Produto) -> Produto:
        await self.session.flush()
        await self.session.refresh(produto)
        return produto

    async def soft_delete(self, produto: Produto) -> None:
        produto.deleted_at = datetime.now(UTC)
        await self.session.flush()
