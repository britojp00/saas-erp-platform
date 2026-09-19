from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_permissions
from app.db.database import get_db_session
from app.schemas.inventory import (
    ConfirmReservationResponse,
    InventoryListResponse,
    InventoryResponse,
    MovementCreate,
    MovementListResponse,
    MovementResponse,
    ReservationCreate,
    ReservationListResponse,
    ReservationResponse,
)
from app.services.inventory import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


async def get_inventory_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InventoryService:
    return InventoryService(db)


@router.get(
    "",
    response_model=InventoryListResponse,
    dependencies=[
        Depends(require_permissions("inventory.read")),
    ],
)
async def list_inventory(
    current_user: CurrentUser,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    product_id: int | None = Query(default=None),
) -> InventoryListResponse:
    items, total = await service.list_balances(
        current_user.tenant_id,
        page=page,
        page_size=page_size,
        product_id=product_id,
    )
    return InventoryListResponse(
        items=[InventoryResponse.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{product_id}",
    response_model=InventoryResponse,
    dependencies=[
        Depends(require_permissions("inventory.read")),
    ],
)
async def get_inventory(
    product_id: int,
    current_user: CurrentUser,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> InventoryResponse:
    inventory = await service.get_balance(current_user.tenant_id, product_id)
    return InventoryResponse.model_validate(inventory)


@router.get(
    "/movements/list",
    response_model=MovementListResponse,
    dependencies=[
        Depends(require_permissions("inventory.read")),
    ],
)
async def list_movements(
    current_user: CurrentUser,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    product_id: int | None = Query(default=None),
) -> MovementListResponse:
    items, total = await service.list_movements(
        current_user.tenant_id,
        page=page,
        page_size=page_size,
        product_id=product_id,
    )
    return MovementListResponse(
        items=[MovementResponse.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/reservations/list",
    response_model=ReservationListResponse,
    dependencies=[
        Depends(require_permissions("inventory.read")),
    ],
)
async def list_reservations(
    current_user: CurrentUser,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    product_id: int | None = Query(default=None),
) -> ReservationListResponse:
    items, total = await service.list_reservations(
        current_user.tenant_id,
        page=page,
        page_size=page_size,
        product_id=product_id,
    )
    return ReservationListResponse(
        items=[ReservationResponse.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "/movements",
    response_model=MovementResponse,
    status_code=201,
    dependencies=[
        Depends(require_permissions("inventory.update")),
    ],
)
async def create_movement(
    data: MovementCreate,
    current_user: CurrentUser,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> MovementResponse:
    movement = await service.create_movement(current_user.tenant_id, data)
    return MovementResponse.model_validate(movement)


@router.post(
    "/reservations",
    response_model=ReservationResponse,
    status_code=201,
    dependencies=[
        Depends(require_permissions("inventory.update")),
    ],
)
async def create_reservation(
    data: ReservationCreate,
    current_user: CurrentUser,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> ReservationResponse:
    reservation = await service.create_reservation(current_user.tenant_id, data)
    return ReservationResponse.model_validate(reservation)


@router.post(
    "/reservations/{reservation_id}/confirm",
    response_model=ConfirmReservationResponse,
    dependencies=[
        Depends(require_permissions("inventory.update")),
    ],
)
async def confirm_reservation(
    reservation_id: int,
    current_user: CurrentUser,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> ConfirmReservationResponse:
    reservation = await service.confirm_reservation(
        current_user.tenant_id, reservation_id
    )
    return ConfirmReservationResponse.model_validate(reservation)


@router.post(
    "/reservations/{reservation_id}/release",
    response_model=ConfirmReservationResponse,
    dependencies=[
        Depends(require_permissions("inventory.update")),
    ],
)
async def release_reservation(
    reservation_id: int,
    current_user: CurrentUser,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> ConfirmReservationResponse:
    reservation = await service.release_reservation(
        current_user.tenant_id, reservation_id
    )
    return ConfirmReservationResponse.model_validate(reservation)


@router.post(
    "/reservations/{reservation_id}/cancel",
    response_model=ConfirmReservationResponse,
    dependencies=[
        Depends(require_permissions("inventory.update")),
    ],
)
async def cancel_reservation(
    reservation_id: int,
    current_user: CurrentUser,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> ConfirmReservationResponse:
    reservation = await service.cancel_reservation(
        current_user.tenant_id, reservation_id
    )
    return ConfirmReservationResponse.model_validate(reservation)
