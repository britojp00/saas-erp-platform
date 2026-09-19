from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_permissions
from app.db.database import get_db_session
from app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
    OrderItemResponse,
    OrderItemUpdate,
    OrderListItem,
    OrderListResponse,
    OrderResponse,
    OrderUpdate,
)
from app.services.order import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


async def get_order_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> OrderService:
    return OrderService(db)


@router.get(
    "",
    response_model=OrderListResponse,
    dependencies=[
        Depends(require_permissions("order.read")),
    ],
)
async def list_orders(
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=150),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    status: str | None = Query(default=None),
    customer_id: int | None = Query(default=None),
) -> OrderListResponse:
    items, total = await service.list(
        current_user.tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
        status=status,
        customer_id=customer_id,
    )
    return OrderListResponse(
        items=[OrderListItem.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    dependencies=[
        Depends(require_permissions("order.read")),
    ],
)
async def get_order(
    order_id: int,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    order = await service.get_with_items(current_user.tenant_id, order_id)
    return OrderResponse.model_validate(order)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=201,
    dependencies=[
        Depends(require_permissions("order.create")),
    ],
)
async def create_order(
    data: OrderCreate,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    order = await service.create(current_user.tenant_id, data)
    order = await service.get_with_items(current_user.tenant_id, order.id)
    return OrderResponse.model_validate(order)


@router.patch(
    "/{order_id}",
    response_model=OrderResponse,
    dependencies=[
        Depends(require_permissions("order.update")),
    ],
)
async def update_order(
    order_id: int,
    data: OrderUpdate,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    order = await service.update(current_user.tenant_id, order_id, data)
    order = await service.get_with_items(current_user.tenant_id, order.id)
    return OrderResponse.model_validate(order)


@router.post(
    "/{order_id}/items",
    response_model=OrderItemResponse,
    status_code=201,
    dependencies=[
        Depends(require_permissions("order.update")),
    ],
)
async def add_order_item(
    order_id: int,
    data: OrderItemCreate,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderItemResponse:
    item = await service.add_item(current_user.tenant_id, order_id, data)
    return OrderItemResponse.model_validate(item)


@router.patch(
    "/{order_id}/items/{item_id}",
    response_model=OrderItemResponse,
    dependencies=[
        Depends(require_permissions("order.update")),
    ],
)
async def update_order_item(
    order_id: int,
    item_id: int,
    data: OrderItemUpdate,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderItemResponse:
    item = await service.update_item(current_user.tenant_id, order_id, item_id, data)
    return OrderItemResponse.model_validate(item)


@router.delete(
    "/{order_id}/items/{item_id}",
    status_code=204,
    dependencies=[
        Depends(require_permissions("order.update")),
    ],
)
async def remove_order_item(
    order_id: int,
    item_id: int,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> None:
    await service.remove_item(current_user.tenant_id, order_id, item_id)


@router.post(
    "/{order_id}/confirm",
    response_model=OrderResponse,
    dependencies=[
        Depends(require_permissions("order.update")),
    ],
)
async def confirm_order(
    order_id: int,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    order = await service.confirm(current_user.tenant_id, order_id)
    order = await service.get_with_items(current_user.tenant_id, order.id)
    return OrderResponse.model_validate(order)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    dependencies=[
        Depends(require_permissions("order.cancel")),
    ],
)
async def cancel_order(
    order_id: int,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    order = await service.cancel(current_user.tenant_id, order_id)
    order = await service.get_with_items(current_user.tenant_id, order.id)
    return OrderResponse.model_validate(order)


@router.post(
    "/{order_id}/complete",
    response_model=OrderResponse,
    dependencies=[
        Depends(require_permissions("order.update")),
    ],
)
async def complete_order(
    order_id: int,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    order = await service.complete(current_user.tenant_id, order_id)
    order = await service.get_with_items(current_user.tenant_id, order.id)
    return OrderResponse.model_validate(order)
