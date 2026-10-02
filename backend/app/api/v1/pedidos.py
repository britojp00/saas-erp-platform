from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_permissions
from app.db.database import get_db_session
from app.schemas.pedido import (
    ListaPedidosResposta,
    PedidoAtualizarPayload,
    PedidoCriarPayload,
    PedidoItemAtualizarPayload,
    PedidoItemCriarPayload,
    PedidoItemResposta,
    PedidoResposta,
    PedidoResumo,
)
from app.services.pedido import PedidoService

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


async def get_pedido_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PedidoService:
    return PedidoService(db)


@router.get(
    "",
    response_model=ListaPedidosResposta,
    dependencies=[
        Depends(require_permissions("pedido.ler")),
    ],
)
async def list_pedidos(
    current_user: CurrentUser,
    service: Annotated[PedidoService, Depends(get_pedido_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=150),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    status: str | None = Query(default=None),
    cliente_id: int | None = Query(default=None),
) -> ListaPedidosResposta:
    items, total = await service.listar_pedidos(
        current_user.tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
        status=status,
        cliente_id=cliente_id,
    )
    return ListaPedidosResposta(
        itens=[PedidoResumo.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{pedido_id}",
    response_model=PedidoResposta,
    dependencies=[
        Depends(require_permissions("pedido.ler")),
    ],
)
async def get_pedido(
    pedido_id: int,
    current_user: CurrentUser,
    service: Annotated[PedidoService, Depends(get_pedido_service)],
) -> PedidoResposta:
    pedido = await service.obter_pedido_com_itens(current_user.tenant_id, pedido_id)
    return PedidoResposta.model_validate(pedido)


@router.post(
    "",
    response_model=PedidoResposta,
    status_code=201,
    dependencies=[
        Depends(require_permissions("pedido.criar")),
    ],
)
async def create_pedido(
    data: PedidoCriarPayload,
    current_user: CurrentUser,
    service: Annotated[PedidoService, Depends(get_pedido_service)],
) -> PedidoResposta:
    pedido = await service.criar_pedido(
        current_user.tenant_id, data, user_id=current_user.id
    )
    pedido = await service.obter_pedido_com_itens(current_user.tenant_id, pedido.id)
    return PedidoResposta.model_validate(pedido)


@router.patch(
    "/{pedido_id}",
    response_model=PedidoResposta,
    dependencies=[
        Depends(require_permissions("pedido.atualizar")),
    ],
)
async def update_pedido(
    pedido_id: int,
    data: PedidoAtualizarPayload,
    current_user: CurrentUser,
    service: Annotated[PedidoService, Depends(get_pedido_service)],
) -> PedidoResposta:
    pedido = await service.atualizar_pedido(
        current_user.tenant_id, pedido_id, data, user_id=current_user.id
    )
    pedido = await service.obter_pedido_com_itens(current_user.tenant_id, pedido.id)
    return PedidoResposta.model_validate(pedido)


@router.post(
    "/{pedido_id}/itens",
    response_model=PedidoItemResposta,
    status_code=201,
    dependencies=[
        Depends(require_permissions("pedido.atualizar")),
    ],
)
async def add_pedido_item(
    pedido_id: int,
    data: PedidoItemCriarPayload,
    current_user: CurrentUser,
    service: Annotated[PedidoService, Depends(get_pedido_service)],
) -> PedidoItemResposta:
    item = await service.adicionar_item(
        current_user.tenant_id, pedido_id, data, user_id=current_user.id
    )
    return PedidoItemResposta.model_validate(item)


@router.patch(
    "/{pedido_id}/itens/{pedido_item_id}",
    response_model=PedidoItemResposta,
    dependencies=[
        Depends(require_permissions("pedido.atualizar")),
    ],
)
async def update_pedido_item(
    pedido_id: int,
    pedido_item_id: int,
    data: PedidoItemAtualizarPayload,
    current_user: CurrentUser,
    service: Annotated[PedidoService, Depends(get_pedido_service)],
) -> PedidoItemResposta:
    item = await service.atualizar_item(
        current_user.tenant_id, pedido_id, pedido_item_id, data, user_id=current_user.id
    )
    return PedidoItemResposta.model_validate(item)


@router.delete(
    "/{pedido_id}/itens/{pedido_item_id}",
    status_code=204,
    dependencies=[
        Depends(require_permissions("pedido.atualizar")),
    ],
)
async def remove_pedido_item(
    pedido_id: int,
    pedido_item_id: int,
    current_user: CurrentUser,
    service: Annotated[PedidoService, Depends(get_pedido_service)],
) -> None:
    await service.remover_item(
        current_user.tenant_id, pedido_id, pedido_item_id, user_id=current_user.id
    )


@router.post(
    "/{pedido_id}/confirmar",
    response_model=PedidoResposta,
    dependencies=[
        Depends(require_permissions("pedido.atualizar")),
    ],
)
async def confirm_pedido(
    pedido_id: int,
    current_user: CurrentUser,
    service: Annotated[PedidoService, Depends(get_pedido_service)],
) -> PedidoResposta:
    pedido = await service.confirmar_pedido(
        current_user.tenant_id, pedido_id, user_id=current_user.id
    )
    pedido = await service.obter_pedido_com_itens(current_user.tenant_id, pedido.id)
    return PedidoResposta.model_validate(pedido)


@router.post(
    "/{pedido_id}/cancelar",
    response_model=PedidoResposta,
    dependencies=[
        Depends(require_permissions("pedido.cancelar")),
    ],
)
async def cancel_pedido(
    pedido_id: int,
    current_user: CurrentUser,
    service: Annotated[PedidoService, Depends(get_pedido_service)],
) -> PedidoResposta:
    pedido = await service.cancelar_pedido(
        current_user.tenant_id, pedido_id, user_id=current_user.id
    )
    pedido = await service.obter_pedido_com_itens(current_user.tenant_id, pedido.id)
    return PedidoResposta.model_validate(pedido)


@router.post(
    "/{pedido_id}/concluir",
    response_model=PedidoResposta,
    dependencies=[
        Depends(require_permissions("pedido.atualizar")),
    ],
)
async def complete_pedido(
    pedido_id: int,
    current_user: CurrentUser,
    service: Annotated[PedidoService, Depends(get_pedido_service)],
) -> PedidoResposta:
    pedido = await service.concluir_pedido(
        current_user.tenant_id, pedido_id, user_id=current_user.id
    )
    pedido = await service.obter_pedido_com_itens(current_user.tenant_id, pedido.id)
    return PedidoResposta.model_validate(pedido)
