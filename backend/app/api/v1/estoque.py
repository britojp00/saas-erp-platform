from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_permissions
from app.db.database import get_db_session
from app.schemas.estoque import (
    ConfirmarReservaResposta,
    EstoqueResposta,
    ListaEstoquesResposta,
    ListaMovimentacoesResposta,
    ListaReservasResposta,
    MovimentacaoCriarPayload,
    MovimentacaoResposta,
    ReservaCriarPayload,
    ReservaResposta,
)
from app.services.estoque import EstoqueService

router = APIRouter(prefix="/estoque", tags=["Estoque"])


async def get_estoque_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> EstoqueService:
    return EstoqueService(db)


@router.get(
    "",
    response_model=ListaEstoquesResposta,
    dependencies=[
        Depends(require_permissions("estoque.ler")),
    ],
)
async def list_estoque(
    current_user: CurrentUser,
    service: Annotated[EstoqueService, Depends(get_estoque_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    produto_id: int | None = Query(default=None),
) -> ListaEstoquesResposta:
    items, total = await service.list_saldos(
        current_user.tenant_id,
        page=page,
        page_size=page_size,
        produto_id=produto_id,
    )
    return ListaEstoquesResposta(
        items=[EstoqueResposta.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{produto_id}",
    response_model=EstoqueResposta,
    dependencies=[
        Depends(require_permissions("estoque.ler")),
    ],
)
async def get_estoque(
    produto_id: int,
    current_user: CurrentUser,
    service: Annotated[EstoqueService, Depends(get_estoque_service)],
) -> EstoqueResposta:
    estoque = await service.get_saldo(current_user.tenant_id, produto_id)
    return EstoqueResposta.model_validate(estoque)


@router.get(
    "/movimentacoes/list",
    response_model=ListaMovimentacoesResposta,
    dependencies=[
        Depends(require_permissions("estoque.ler")),
    ],
)
async def list_movimentacoes(
    current_user: CurrentUser,
    service: Annotated[EstoqueService, Depends(get_estoque_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    produto_id: int | None = Query(default=None),
) -> ListaMovimentacoesResposta:
    items, total = await service.list_movimentacoes(
        current_user.tenant_id,
        page=page,
        page_size=page_size,
        produto_id=produto_id,
    )
    return ListaMovimentacoesResposta(
        items=[MovimentacaoResposta.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/reservas/list",
    response_model=ListaReservasResposta,
    dependencies=[
        Depends(require_permissions("estoque.ler")),
    ],
)
async def list_reservas(
    current_user: CurrentUser,
    service: Annotated[EstoqueService, Depends(get_estoque_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    produto_id: int | None = Query(default=None),
) -> ListaReservasResposta:
    items, total = await service.list_reservas(
        current_user.tenant_id,
        page=page,
        page_size=page_size,
        produto_id=produto_id,
    )
    return ListaReservasResposta(
        items=[ReservaResposta.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "/movimentacoes",
    response_model=MovimentacaoResposta,
    status_code=201,
    dependencies=[
        Depends(require_permissions("estoque.atualizar")),
    ],
)
async def create_movimentacao(
    data: MovimentacaoCriarPayload,
    current_user: CurrentUser,
    service: Annotated[EstoqueService, Depends(get_estoque_service)],
) -> MovimentacaoResposta:
    movimentacao = await service.create_movimentacao(
        current_user.tenant_id, data, user_id=current_user.id
    )
    return MovimentacaoResposta.model_validate(movimentacao)


@router.post(
    "/reservas",
    response_model=ReservaResposta,
    status_code=201,
    dependencies=[
        Depends(require_permissions("estoque.atualizar")),
    ],
)
async def create_reserva(
    data: ReservaCriarPayload,
    current_user: CurrentUser,
    service: Annotated[EstoqueService, Depends(get_estoque_service)],
) -> ReservaResposta:
    reserva = await service.create_reserva(
        current_user.tenant_id, data, user_id=current_user.id
    )
    return ReservaResposta.model_validate(reserva)


@router.post(
    "/reservas/{reserva_id}/confirmar",
    response_model=ConfirmarReservaResposta,
    dependencies=[
        Depends(require_permissions("estoque.atualizar")),
    ],
)
async def confirm_reserva(
    reserva_id: int,
    current_user: CurrentUser,
    service: Annotated[EstoqueService, Depends(get_estoque_service)],
) -> ConfirmarReservaResposta:
    reserva = await service.confirm_reserva(
        current_user.tenant_id, reserva_id, user_id=current_user.id
    )
    return ConfirmarReservaResposta.model_validate(reserva)


@router.post(
    "/reservas/{reserva_id}/liberar",
    response_model=ConfirmarReservaResposta,
    dependencies=[
        Depends(require_permissions("estoque.atualizar")),
    ],
)
async def release_reserva(
    reserva_id: int,
    current_user: CurrentUser,
    service: Annotated[EstoqueService, Depends(get_estoque_service)],
) -> ConfirmarReservaResposta:
    reserva = await service.release_reserva(
        current_user.tenant_id, reserva_id, user_id=current_user.id
    )
    return ConfirmarReservaResposta.model_validate(reserva)


@router.post(
    "/reservas/{reserva_id}/cancelar",
    response_model=ConfirmarReservaResposta,
    dependencies=[
        Depends(require_permissions("estoque.atualizar")),
    ],
)
async def cancel_reserva(
    reserva_id: int,
    current_user: CurrentUser,
    service: Annotated[EstoqueService, Depends(get_estoque_service)],
) -> ConfirmarReservaResposta:
    reserva = await service.cancel_reserva(
        current_user.tenant_id, reserva_id, user_id=current_user.id
    )
    return ConfirmarReservaResposta.model_validate(reserva)
