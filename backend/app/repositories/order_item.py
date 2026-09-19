from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order_item import OrderItem


class OrderItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_order(
        self,
        tenant_id: int,
        order_id: int,
    ) -> list[OrderItem]:
        stmt = (
            select(OrderItem)
            .where(
                OrderItem.tenant_id == tenant_id,
                OrderItem.order_id == order_id,
            )
            .order_by(OrderItem.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        tenant_id: int,
        item_id: int,
    ) -> OrderItem | None:
        stmt = select(OrderItem).where(
            OrderItem.id == item_id,
            OrderItem.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_order(
        self,
        tenant_id: int,
        item_id: int,
        order_id: int,
    ) -> OrderItem | None:
        stmt = select(OrderItem).where(
            OrderItem.id == item_id,
            OrderItem.tenant_id == tenant_id,
            OrderItem.order_id == order_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_product_in_order(
        self,
        tenant_id: int,
        order_id: int,
        product_id: int,
        exclude_item_id: int | None = None,
    ) -> bool:
        stmt = select(OrderItem).where(
            OrderItem.tenant_id == tenant_id,
            OrderItem.order_id == order_id,
            OrderItem.product_id == product_id,
        )
        if exclude_item_id is not None:
            stmt = stmt.where(OrderItem.id != exclude_item_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def count_by_order(
        self,
        tenant_id: int,
        order_id: int,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(OrderItem)
            .where(
                OrderItem.tenant_id == tenant_id,
                OrderItem.order_id == order_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, item: OrderItem) -> OrderItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def update(self, item: OrderItem) -> OrderItem:
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def delete(self, item: OrderItem) -> None:
        await self.session.delete(item)
        await self.session.flush()
