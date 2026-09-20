from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CategoryCycleError,
    CategoryHasChildrenError,
    CategoryHasProductsError,
    CategoryNotFoundError,
    CategoryParentNotFoundError,
    CategorySelfReferenceError,
    DuplicateCategoryError,
)
from app.db.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.audit_log import AuditLogService


class CategoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CategoryRepository(session)
        self.audit_service = AuditLogService(session)

    async def list(
        self,
        tenant_id: int,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[Category], int]:
        offset = (page - 1) * page_size
        return await self.repo.list(
            tenant_id,
            offset=offset,
            limit=page_size,
            search=search,
            sort=sort,
            order=order,
        )

    async def get_by_id(
        self,
        category_id: int,
        tenant_id: int,
    ) -> Category:
        category = await self.repo.get_by_id(category_id, tenant_id)
        if category is None:
            raise CategoryNotFoundError()
        return category

    async def _validate_parent(
        self,
        tenant_id: int,
        parent_id: int | None,
        exclude_id: int | None = None,
    ) -> None:
        if parent_id is None:
            return

        if parent_id == exclude_id:
            raise CategorySelfReferenceError()

        parent = await self.repo.get_by_id(parent_id, tenant_id)
        if parent is None:
            raise CategoryParentNotFoundError()

        if exclude_id is not None:
            ancestors = await self.repo.get_ancestor_ids(tenant_id, parent_id)
            if exclude_id in ancestors:
                raise CategoryCycleError()

    async def create(
        self,
        tenant_id: int,
        data: CategoryCreate,
        user_id: int | None = None,
    ) -> Category:
        if data.parent_id is not None:
            await self._validate_parent(tenant_id, data.parent_id)

        if await self.repo.exists_by_name(tenant_id, data.name.strip()):
            raise DuplicateCategoryError()

        category = Category(
            tenant_id=tenant_id,
            name=data.name.strip(),
            description=data.description,
            parent_id=data.parent_id,
        )

        try:
            result = await self.repo.create(category)
        except IntegrityError:
            raise DuplicateCategoryError()

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="CATEGORY_CREATE",
            entity_type="category",
            entity_id=result.id,
            new_values={
                "name": result.name,
                "description": result.description,
                "parent_id": result.parent_id,
            },
        )

        return result

    async def update(
        self,
        category_id: int,
        tenant_id: int,
        data: CategoryUpdate,
        user_id: int | None = None,
    ) -> Category:
        category = await self.repo.get_by_id(category_id, tenant_id)
        if category is None:
            raise CategoryNotFoundError()

        old_values = {
            "name": category.name,
            "description": category.description,
            "parent_id": category.parent_id,
        }

        update_data = data.model_dump(exclude_unset=True)

        if "parent_id" in update_data:
            new_parent_id = update_data["parent_id"]
            await self._validate_parent(
                tenant_id, new_parent_id, exclude_id=category.id
            )
            category.parent_id = new_parent_id

        if "name" in update_data:
            new_name = update_data["name"].strip()
            if new_name != category.name and await self.repo.exists_by_name(
                tenant_id, new_name, exclude_id=category.id
            ):
                raise DuplicateCategoryError()
            category.name = new_name
        if "description" in update_data:
            category.description = update_data["description"]

        try:
            result = await self.repo.update(category)
        except IntegrityError:
            raise DuplicateCategoryError()

        new_values = {
            "name": result.name,
            "description": result.description,
            "parent_id": result.parent_id,
        }

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="CATEGORY_UPDATE",
            entity_type="category",
            entity_id=result.id,
            old_values=old_values,
            new_values=new_values,
        )

        return result

    async def soft_delete(
        self,
        category_id: int,
        tenant_id: int,
        user_id: int | None = None,
    ) -> None:
        category = await self.repo.get_by_id(category_id, tenant_id)
        if category is None:
            raise CategoryNotFoundError()

        if await self.repo.has_children(tenant_id, category.id):
            raise CategoryHasChildrenError()

        if await self.repo.has_products(tenant_id, category.id):
            raise CategoryHasProductsError()

        old_values = {
            "name": category.name,
            "description": category.description,
        }

        await self.repo.soft_delete(category)

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="CATEGORY_DELETE",
            entity_type="category",
            entity_id=category_id,
            old_values=old_values,
        )
