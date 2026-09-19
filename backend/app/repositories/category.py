from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.category import Category
from app.db.models.product import Product

SORT_FIELDS = {
    "name": Category.name,
    "created_at": Category.created_at,
}


class CategoryRepository:
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
    ) -> tuple[list[Category], int]:
        base_stmt = select(Category).where(
            Category.tenant_id == tenant_id,
            Category.deleted_at.is_(None),
        )
        if search:
            base_stmt = base_stmt.where(Category.name.ilike(f"%{search}%"))

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        sort_column = SORT_FIELDS.get(sort, Category.created_at)
        if order == "asc":
            base_stmt = base_stmt.order_by(sort_column.asc(), Category.id.asc())
        else:
            base_stmt = base_stmt.order_by(sort_column.desc(), Category.id.desc())

        base_stmt = base_stmt.offset(offset).limit(limit)
        result = await self.session.execute(base_stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_by_id(
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

    async def exists_by_name(
        self,
        tenant_id: int,
        name: str,
        exclude_id: int | None = None,
    ) -> bool:
        stmt = select(Category).where(
            Category.tenant_id == tenant_id,
            Category.name == name,
        )
        if exclude_id is not None:
            stmt = stmt.where(Category.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_children_ids(
        self,
        tenant_id: int,
        parent_id: int,
    ) -> set[int]:
        stmt = select(Category.id).where(
            Category.tenant_id == tenant_id,
            Category.parent_id == parent_id,
            Category.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())

    async def get_ancestor_ids(
        self,
        tenant_id: int,
        category_id: int,
    ) -> set[int]:
        ancestors: set[int] = set()
        current_parent_id = category_id
        while True:
            stmt = select(Category.parent_id).where(
                Category.id == current_parent_id,
                Category.tenant_id == tenant_id,
                Category.deleted_at.is_(None),
            )
            result = await self.session.execute(stmt)
            parent_id = result.scalar_one_or_none()
            if parent_id is None:
                break
            if parent_id in ancestors:
                break
            ancestors.add(parent_id)
            current_parent_id = parent_id
        return ancestors

    async def has_children(
        self,
        tenant_id: int,
        category_id: int,
    ) -> bool:
        children = await self.get_children_ids(tenant_id, category_id)
        return len(children) > 0

    async def has_products(
        self,
        tenant_id: int,
        category_id: int,
    ) -> bool:
        stmt = (
            select(Product)
            .where(
                Product.tenant_id == tenant_id,
                Product.category_id == category_id,
                Product.deleted_at.is_(None),
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, category: Category) -> Category:
        self.session.add(category)
        await self.session.flush()
        return category

    async def update(self, category: Category) -> Category:
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def soft_delete(self, category: Category) -> None:
        category.deleted_at = datetime.now(UTC)
        await self.session.flush()
