from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.pedido_item import PedidoItem


class PedidoItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def listar_por_pedido(
        self,
        empresa_id: int,
        pedido_id: int,
    ) -> list[PedidoItem]:
        stmt = (
            select(PedidoItem)
            .where(
                PedidoItem.empresa_id == empresa_id,
                PedidoItem.pedido_id == pedido_id,
            )
            .order_by(PedidoItem.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        empresa_id: int,
        item_id: int,
    ) -> PedidoItem | None:
        stmt = select(PedidoItem).where(
            PedidoItem.id == item_id,
            PedidoItem.empresa_id == empresa_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def obter_por_id_e_pedido(
        self,
        empresa_id: int,
        item_id: int,
        pedido_id: int,
    ) -> PedidoItem | None:
        stmt = select(PedidoItem).where(
            PedidoItem.id == item_id,
            PedidoItem.empresa_id == empresa_id,
            PedidoItem.pedido_id == pedido_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def existe_produto_no_pedido(
        self,
        empresa_id: int,
        pedido_id: int,
        produto_id: int,
        exclude_item_id: int | None = None,
    ) -> bool:
        stmt = select(PedidoItem).where(
            PedidoItem.empresa_id == empresa_id,
            PedidoItem.pedido_id == pedido_id,
            PedidoItem.produto_id == produto_id,
        )
        if exclude_item_id is not None:
            stmt = stmt.where(PedidoItem.id != exclude_item_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def contar_por_pedido(
        self,
        empresa_id: int,
        pedido_id: int,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(PedidoItem)
            .where(
                PedidoItem.empresa_id == empresa_id,
                PedidoItem.pedido_id == pedido_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, item: PedidoItem) -> PedidoItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def update(self, item: PedidoItem) -> PedidoItem:
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def delete(self, item: PedidoItem) -> None:
        await self.session.delete(item)
        await self.session.flush()
