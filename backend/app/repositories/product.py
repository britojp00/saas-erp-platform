from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.category import Category
from app.db.models.inventory import Inventory
from app.db.models.order_item import OrderItem
from app.db.models.product import Product

SORT_FIELDS = {
    "name": Product.name,
    "sku": Product.sku,
    "price": Product.price,
    "is_active": Product.is_active,
    "created_at": Product.created_at,
}


class ProductRepository:
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
        category_id: int | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Product], int]:
        base_stmt = select(Product).where(
            Product.tenant_id == tenant_id,
            Product.deleted_at.is_(None),
        )
        if search:
            base_stmt = base_stmt.where(
                Product.name.ilike(f"%{search}%") | Product.sku.ilike(f"%{search}%")
            )
        if category_id is not None:
            base_stmt = base_stmt.where(Product.category_id == category_id)
        if is_active is not None:
            base_stmt = base_stmt.where(Product.is_active == is_active)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        sort_column = SORT_FIELDS.get(sort, Product.created_at)
        if order == "asc":
            base_stmt = base_stmt.order_by(sort_column.asc(), Product.id.asc())
        else:
            base_stmt = base_stmt.order_by(sort_column.desc(), Product.id.desc())

        base_stmt = base_stmt.offset(offset).limit(limit)
        result = await self.session.execute(base_stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_by_id(
        self,
        product_id: int,
        tenant_id: int,
    ) -> Product | None:
        stmt = select(Product).where(
            Product.id == product_id,
            Product.tenant_id == tenant_id,
            Product.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_category_by_id(
        self,
        category_id: int,
        tenant_id: int,
    ) -> Category | None:
        stmt = select(Category).where(
            Category.id == category_id,
            Category.tenant_id == tenant_id,
            Category.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_sku(
        self,
        tenant_id: int,
        sku: str,
        exclude_id: int | None = None,
    ) -> bool:
        stmt = select(Product).where(
            Product.tenant_id == tenant_id,
            Product.sku == sku,
        )
        if exclude_id is not None:
            stmt = stmt.where(Product.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def has_inventory(
        self,
        tenant_id: int,
        product_id: int,
    ) -> bool:
        stmt = (
            select(Inventory)
            .where(
                Inventory.tenant_id == tenant_id,
                Inventory.product_id == product_id,
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def has_order_items(
        self,
        tenant_id: int,
        product_id: int,
    ) -> bool:
        stmt = (
            select(OrderItem)
            .where(
                OrderItem.tenant_id == tenant_id,
                OrderItem.product_id == product_id,
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.flush()
        return product

    async def update(self, product: Product) -> Product:
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def soft_delete(self, product: Product) -> None:
        product.deleted_at = datetime.now(UTC)
        await self.session.flush()
