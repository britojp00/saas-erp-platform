from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DuplicateProductError,
    InvalidProductCategoryError,
    ProductInUseError,
    ProductNotFoundError,
)
from app.db.models.product import Product
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.audit_log import AuditLogService


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProductRepository(session)
        self.audit_service = AuditLogService(session)

    async def _validate_category(
        self,
        tenant_id: int,
        category_id: int | None,
    ) -> None:
        if category_id is None:
            return
        category = await self.repo.get_category_by_id(category_id, tenant_id)
        if category is None:
            raise InvalidProductCategoryError()

    async def list(
        self,
        tenant_id: int,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
        category_id: int | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Product], int]:
        offset = (page - 1) * page_size
        return await self.repo.list(
            tenant_id,
            offset=offset,
            limit=page_size,
            search=search,
            sort=sort,
            order=order,
            category_id=category_id,
            is_active=is_active,
        )

    async def get_by_id(
        self,
        product_id: int,
        tenant_id: int,
    ) -> Product:
        product = await self.repo.get_by_id(product_id, tenant_id)
        if product is None:
            raise ProductNotFoundError()
        return product

    async def create(
        self,
        tenant_id: int,
        data: ProductCreate,
        user_id: int | None = None,
    ) -> Product:
        await self._validate_category(tenant_id, data.category_id)

        if await self.repo.exists_by_sku(tenant_id, data.sku.strip()):
            raise DuplicateProductError()

        product = Product(
            tenant_id=tenant_id,
            sku=data.sku.strip(),
            name=data.name.strip(),
            description=data.description,
            category_id=data.category_id,
            price=data.price,
            cost_price=data.cost_price,
            is_active=data.is_active,
        )

        try:
            result = await self.repo.create(product)
        except IntegrityError:
            raise DuplicateProductError()

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="PRODUCT_CREATE",
            entity_type="product",
            entity_id=result.id,
            new_values={
                "sku": result.sku,
                "name": result.name,
                "price": str(result.price),
                "is_active": result.is_active,
            },
        )

        return result

    async def update(
        self,
        product_id: int,
        tenant_id: int,
        data: ProductUpdate,
        user_id: int | None = None,
    ) -> Product:
        product = await self.repo.get_by_id(product_id, tenant_id)
        if product is None:
            raise ProductNotFoundError()

        old_values = {
            "sku": product.sku,
            "name": product.name,
            "price": str(product.price),
            "is_active": product.is_active,
        }

        update_data = data.model_dump(exclude_unset=True)

        if "category_id" in update_data:
            new_category_id = update_data["category_id"]
            if new_category_id is not None:
                await self._validate_category(tenant_id, new_category_id)
            product.category_id = new_category_id

        if "sku" in update_data:
            new_sku = update_data["sku"].strip()
            if new_sku != product.sku and await self.repo.exists_by_sku(
                tenant_id, new_sku, exclude_id=product.id
            ):
                raise DuplicateProductError()
            product.sku = new_sku

        if "name" in update_data:
            product.name = update_data["name"].strip()
        if "description" in update_data:
            product.description = update_data["description"]
        if "price" in update_data:
            product.price = update_data["price"]
        if "cost_price" in update_data:
            product.cost_price = update_data["cost_price"]
        if "is_active" in update_data:
            product.is_active = update_data["is_active"]

        try:
            result = await self.repo.update(product)
        except IntegrityError:
            raise DuplicateProductError()

        new_values = {
            "sku": result.sku,
            "name": result.name,
            "price": str(result.price),
            "is_active": result.is_active,
        }

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="PRODUCT_UPDATE",
            entity_type="product",
            entity_id=result.id,
            old_values=old_values,
            new_values=new_values,
        )

        return result

    async def soft_delete(
        self,
        product_id: int,
        tenant_id: int,
        user_id: int | None = None,
    ) -> None:
        product = await self.repo.get_by_id(product_id, tenant_id)
        if product is None:
            raise ProductNotFoundError()

        if await self.repo.has_inventory(tenant_id, product.id):
            raise ProductInUseError()

        if await self.repo.has_order_items(tenant_id, product.id):
            raise ProductInUseError()

        old_values = {
            "sku": product.sku,
            "name": product.name,
        }

        await self.repo.soft_delete(product)

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="PRODUCT_DELETE",
            entity_type="product",
            entity_id=product_id,
            old_values=old_values,
        )
