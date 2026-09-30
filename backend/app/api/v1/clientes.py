from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_permissions
from app.db.database import get_db_session
from app.schemas.cliente import (
    ClienteAtualizarPayload,
    ClienteCriarPayload,
    ClienteResposta,
    ListaClientesResposta,
)
from app.services.cliente import ClienteService

router = APIRouter(prefix="/clientes", tags=["Clientes"])


async def get_cliente_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ClienteService:
    return ClienteService(db)


@router.get(
    "",
    response_model=ListaClientesResposta,
    dependencies=[
        Depends(require_permissions("cliente.ler")),
    ],
)
async def list_clientes(
    current_user: CurrentUser,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=150),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
) -> ListaClientesResposta:
    items, total = await service.list(
        current_user.tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    return ListaClientesResposta(
        items=[ClienteResposta.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{cliente_id}",
    response_model=ClienteResposta,
    dependencies=[
        Depends(require_permissions("cliente.ler")),
    ],
)
async def get_cliente(
    cliente_id: int,
    current_user: CurrentUser,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
) -> ClienteResposta:
    cliente = await service.get_by_id(cliente_id, current_user.tenant_id)
    return ClienteResposta.model_validate(cliente)


@router.post(
    "",
    response_model=ClienteResposta,
    status_code=201,
    dependencies=[
        Depends(require_permissions("cliente.criar")),
    ],
)
async def create_cliente(
    data: ClienteCriarPayload,
    current_user: CurrentUser,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
) -> ClienteResposta:
    cliente = await service.create(
        current_user.tenant_id, data, user_id=current_user.id
    )
    return ClienteResposta.model_validate(cliente)


@router.patch(
    "/{cliente_id}",
    response_model=ClienteResposta,
    dependencies=[
        Depends(require_permissions("cliente.atualizar")),
    ],
)
async def update_cliente(
    cliente_id: int,
    data: ClienteAtualizarPayload,
    current_user: CurrentUser,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
) -> ClienteResposta:
    cliente = await service.update(
        cliente_id, current_user.tenant_id, data, user_id=current_user.id
    )
    return ClienteResposta.model_validate(cliente)


@router.delete(
    "/{cliente_id}",
    status_code=204,
    dependencies=[
        Depends(require_permissions("cliente.excluir")),
    ],
)
async def delete_cliente(
    cliente_id: int,
    current_user: CurrentUser,
    service: Annotated[ClienteService, Depends(get_cliente_service)],
) -> None:
    await service.soft_delete(
        cliente_id, current_user.tenant_id, user_id=current_user.id
    )
