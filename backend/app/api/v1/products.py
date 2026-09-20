from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_permissions
from app.db.database import get_db_session
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services.product import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


async def get_product_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProductService:
    return ProductService(db)


@router.get(
    "",
    response_model=ProductListResponse,
    dependencies=[
        Depends(require_permissions("product.read")),
    ],
)
async def list_products(
    current_user: CurrentUser,
    service: Annotated[ProductService, Depends(get_product_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=150),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    category_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
) -> ProductListResponse:
    items, total = await service.list(
        current_user.tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
        category_id=category_id,
        is_active=is_active,
    )
    return ProductListResponse(
        items=[ProductResponse.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[
        Depends(require_permissions("product.read")),
    ],
)
async def get_product(
    product_id: int,
    current_user: CurrentUser,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    product = await service.get_by_id(product_id, current_user.tenant_id)
    return ProductResponse.model_validate(product)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=201,
    dependencies=[
        Depends(require_permissions("product.create")),
    ],
)
async def create_product(
    data: ProductCreate,
    current_user: CurrentUser,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    product = await service.create(
        current_user.tenant_id, data, user_id=current_user.id
    )
    return ProductResponse.model_validate(product)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[
        Depends(require_permissions("product.update")),
    ],
)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    current_user: CurrentUser,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    product = await service.update(
        product_id, current_user.tenant_id, data, user_id=current_user.id
    )
    return ProductResponse.model_validate(product)


@router.delete(
    "/{product_id}",
    status_code=204,
    dependencies=[
        Depends(require_permissions("product.delete")),
    ],
)
async def delete_product(
    product_id: int,
    current_user: CurrentUser,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> None:
    await service.soft_delete(
        product_id, current_user.tenant_id, user_id=current_user.id
    )
