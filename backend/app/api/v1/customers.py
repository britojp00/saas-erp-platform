from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_permissions
from app.db.database import get_db_session
from app.schemas.customer import (
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdate,
)
from app.services.customer import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


async def get_customer_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CustomerService:
    return CustomerService(db)


@router.get(
    "",
    response_model=CustomerListResponse,
    dependencies=[
        Depends(require_permissions("customer.read")),
    ],
)
async def list_customers(
    current_user: CurrentUser,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=150),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
) -> CustomerListResponse:
    items, total = await service.list(
        current_user.tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    return CustomerListResponse(
        items=[CustomerResponse.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    dependencies=[
        Depends(require_permissions("customer.read")),
    ],
)
async def get_customer(
    customer_id: int,
    current_user: CurrentUser,
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerResponse:
    customer = await service.get_by_id(customer_id, current_user.tenant_id)
    return CustomerResponse.model_validate(customer)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=201,
    dependencies=[
        Depends(require_permissions("customer.create")),
    ],
)
async def create_customer(
    data: CustomerCreate,
    current_user: CurrentUser,
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerResponse:
    customer = await service.create(current_user.tenant_id, data)
    return CustomerResponse.model_validate(customer)


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
    dependencies=[
        Depends(require_permissions("customer.update")),
    ],
)
async def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    current_user: CurrentUser,
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerResponse:
    customer = await service.update(customer_id, current_user.tenant_id, data)
    return CustomerResponse.model_validate(customer)


@router.delete(
    "/{customer_id}",
    status_code=204,
    dependencies=[
        Depends(require_permissions("customer.delete")),
    ],
)
async def delete_customer(
    customer_id: int,
    current_user: CurrentUser,
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> None:
    await service.soft_delete(customer_id, current_user.tenant_id)
