from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inventory_movement import InventoryMovement


class InventoryMovementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, movement: InventoryMovement) -> InventoryMovement:
        self.session.add(movement)
        await self.session.flush()
        return movement

    async def list(
        self,
        tenant_id: int,
        *,
        offset: int,
        limit: int,
        product_id: int | None = None,
    ) -> tuple[list[InventoryMovement], int]:
        base_stmt = select(InventoryMovement).where(
            InventoryMovement.tenant_id == tenant_id,
        )
        if product_id is not None:
            base_stmt = base_stmt.where(InventoryMovement.product_id == product_id)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        base_stmt = base_stmt.order_by(
            InventoryMovement.performed_at.desc(), InventoryMovement.id.desc()
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
        stmt = select(InventoryMovement).where(
            InventoryMovement.tenant_id == tenant_id,
            InventoryMovement.idempotency_key == idempotency_key,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
