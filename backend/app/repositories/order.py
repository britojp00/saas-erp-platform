from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order

SORT_FIELDS = {
    "order_number": Order.order_number,
    "status": Order.status,
    "total_amount": Order.total_amount,
    "customer_id": Order.customer_id,
    "created_at": Order.created_at,
    "updated_at": Order.updated_at,
}


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        tenant_id: int,
        *,
        offset: int,
        limit: int,
        search: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
        status: str | None = None,
        customer_id: int | None = None,
    ) -> tuple[list[Order], int]:
        base_stmt = select(Order).where(
            Order.tenant_id == tenant_id,
            Order.deleted_at.is_(None),
        )
        if search:
            base_stmt = base_stmt.where(
                Order.order_number.cast(str).ilike(f"%{search}%")
                | Order.notes.ilike(f"%{search}%")
            )
        if status is not None:
            base_stmt = base_stmt.where(Order.status == status)
        if customer_id is not None:
            base_stmt = base_stmt.where(Order.customer_id == customer_id)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        sort_column = SORT_FIELDS.get(sort, Order.created_at)
        if order == "asc":
            base_stmt = base_stmt.order_by(sort_column.asc(), Order.id.asc())
        else:
            base_stmt = base_stmt.order_by(sort_column.desc(), Order.id.desc())

        base_stmt = base_stmt.offset(offset).limit(limit)
        result = await self.session.execute(base_stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_by_id(
        self,
        tenant_id: int,
        order_id: int,
    ) -> Order | None:
        stmt = select(Order).where(
            Order.id == order_id,
            Order.tenant_id == tenant_id,
            Order.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_update(
        self,
        tenant_id: int,
        order_id: int,
    ) -> Order | None:
        stmt = (
            select(Order)
            .where(
                Order.id == order_id,
                Order.tenant_id == tenant_id,
                Order.deleted_at.is_(None),
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def next_order_number(
        self,
        tenant_id: int,
    ) -> int:
        from sqlalchemy import text

        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:tid))"),
            {"tid": str(tenant_id)},
        )

        stmt = select(func.max(Order.order_number)).where(
            Order.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        max_num = result.scalar_one()

        if max_num is None:
            return 1
        return int(max_num) + 1

    async def create(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.flush()
        return order

    async def update(self, order: Order) -> Order:
        await self.session.flush()
        await self.session.refresh(order)
        return order
