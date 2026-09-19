from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inventory_reservation import InventoryReservation, ReservationStatus


class InventoryReservationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, reservation: InventoryReservation) -> InventoryReservation:
        self.session.add(reservation)
        await self.session.flush()
        return reservation

    async def get_by_id(
        self,
        tenant_id: int,
        reservation_id: int,
    ) -> InventoryReservation | None:
        stmt = select(InventoryReservation).where(
            InventoryReservation.tenant_id == tenant_id,
            InventoryReservation.id == reservation_id,
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
    ) -> tuple[list[InventoryReservation], int]:
        base_stmt = select(InventoryReservation).where(
            InventoryReservation.tenant_id == tenant_id,
        )
        if product_id is not None:
            base_stmt = base_stmt.where(InventoryReservation.product_id == product_id)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        base_stmt = base_stmt.order_by(
            InventoryReservation.reserved_at.desc(),
            InventoryReservation.id.desc(),
        )
        base_stmt = base_stmt.offset(offset).limit(limit)
        result = await self.session.execute(base_stmt)
        items = list(result.scalars().all())

        return items, total

    async def list_active_by_reference(
        self,
        tenant_id: int,
        reference: str,
    ) -> list[InventoryReservation]:
        stmt = (
            select(InventoryReservation)
            .where(
                InventoryReservation.tenant_id == tenant_id,
                InventoryReservation.reference == reference,
                InventoryReservation.status == ReservationStatus.ACTIVE,
            )
            .order_by(InventoryReservation.product_id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def exists_by_idempotency_key(
        self,
        tenant_id: int,
        idempotency_key: str,
    ) -> bool:
        stmt = select(InventoryReservation).where(
            InventoryReservation.tenant_id == tenant_id,
            InventoryReservation.idempotency_key == idempotency_key,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def update(self, reservation: InventoryReservation) -> InventoryReservation:
        await self.session.flush()
        await self.session.refresh(reservation)
        return reservation
