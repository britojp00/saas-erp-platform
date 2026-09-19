from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_permissions
from app.db.database import get_db_session
from app.schemas.category import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdate,
)
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


async def get_category_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CategoryService:
    return CategoryService(db)


@router.get(
    "",
    response_model=CategoryListResponse,
    dependencies=[
        Depends(require_permissions("category.read")),
    ],
)
async def list_categories(
    current_user: CurrentUser,
    service: Annotated[CategoryService, Depends(get_category_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=100),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
) -> CategoryListResponse:
    items, total = await service.list(
        current_user.tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    return CategoryListResponse(
        items=[CategoryResponse.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[
        Depends(require_permissions("category.read")),
    ],
)
async def get_category(
    category_id: int,
    current_user: CurrentUser,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    category = await service.get_by_id(category_id, current_user.tenant_id)
    return CategoryResponse.model_validate(category)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=201,
    dependencies=[
        Depends(require_permissions("category.create")),
    ],
)
async def create_category(
    data: CategoryCreate,
    current_user: CurrentUser,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    category = await service.create(current_user.tenant_id, data)
    return CategoryResponse.model_validate(category)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[
        Depends(require_permissions("category.update")),
    ],
)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    current_user: CurrentUser,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    category = await service.update(category_id, current_user.tenant_id, data)
    return CategoryResponse.model_validate(category)


@router.delete(
    "/{category_id}",
    status_code=204,
    dependencies=[
        Depends(require_permissions("category.delete")),
    ],
)
async def delete_category(
    category_id: int,
    current_user: CurrentUser,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> None:
    await service.soft_delete(category_id, current_user.tenant_id)
