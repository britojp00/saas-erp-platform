from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inventory import Inventory


class InventoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_product_id(
        self,
        tenant_id: int,
        product_id: int,
    ) -> Inventory | None:
        stmt = select(Inventory).where(
            Inventory.tenant_id == tenant_id,
            Inventory.product_id == product_id,
            Inventory.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_update(
        self,
        tenant_id: int,
        product_id: int,
    ) -> Inventory | None:
        stmt = (
            select(Inventory)
            .where(
                Inventory.tenant_id == tenant_id,
                Inventory.product_id == product_id,
                Inventory.deleted_at.is_(None),
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
        product_id: int | None = None,
    ) -> tuple[list[Inventory], int]:
        base_stmt = select(Inventory).where(
            Inventory.tenant_id == tenant_id,
            Inventory.deleted_at.is_(None),
        )
        if product_id is not None:
            base_stmt = base_stmt.where(Inventory.product_id == product_id)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        base_stmt = base_stmt.order_by(Inventory.created_at.desc(), Inventory.id.desc())
        base_stmt = base_stmt.offset(offset).limit(limit)
        result = await self.session.execute(base_stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_or_create(
        self,
        tenant_id: int,
        product_id: int,
    ) -> Inventory:
        inventory = await self.get_by_product_id(tenant_id, product_id)
        if inventory is None:
            inventory = Inventory(
                tenant_id=tenant_id,
                product_id=product_id,
            )
            self.session.add(inventory)
            await self.session.flush()
        return inventory
