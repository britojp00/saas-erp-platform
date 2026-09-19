from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.customer import Customer

SORT_FIELDS = {
    "name": Customer.name,
    "created_at": Customer.created_at,
}


class CustomerRepository:
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
    ) -> tuple[list[Customer], int]:
        base_stmt = select(Customer).where(
            Customer.tenant_id == tenant_id,
            Customer.deleted_at.is_(None),
        )
        if search:
            base_stmt = base_stmt.where(Customer.name.ilike(f"%{search}%"))

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        sort_column = SORT_FIELDS.get(sort, Customer.created_at)
        if order == "asc":
            base_stmt = base_stmt.order_by(sort_column.asc(), Customer.id.asc())
        else:
            base_stmt = base_stmt.order_by(sort_column.desc(), Customer.id.desc())

        base_stmt = base_stmt.offset(offset).limit(limit)
        result = await self.session.execute(base_stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_by_id(
        self,
        customer_id: int,
        tenant_id: int,
    ) -> Customer | None:
        stmt = select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == tenant_id,
            Customer.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_document(
        self,
        tenant_id: int,
        document: str,
        exclude_id: int | None = None,
    ) -> bool:
        stmt = select(Customer).where(
            Customer.tenant_id == tenant_id,
            Customer.document == document,
        )
        if exclude_id is not None:
            stmt = stmt.where(Customer.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, customer: Customer) -> Customer:
        self.session.add(customer)
        await self.session.flush()
        return customer

    async def update(self, customer: Customer) -> Customer:
        await self.session.flush()
        await self.session.refresh(customer)
        return customer

    async def soft_delete(self, customer: Customer) -> None:
        customer.deleted_at = datetime.now(UTC)
        await self.session.flush()
