from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_permissions
from app.db.database import get_db_session
from app.schemas.produto import (
    ListaProdutosResposta,
    ProdutoAtualizarPayload,
    ProdutoCriarPayload,
    ProdutoResposta,
)
from app.services.produto import ProdutoService

router = APIRouter(prefix="/produtos", tags=["Produtos"])


async def get_produto_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProdutoService:
    return ProdutoService(db)


@router.get(
    "",
    response_model=ListaProdutosResposta,
    dependencies=[
        Depends(require_permissions("produto.ler")),
    ],
)
async def list_produtos(
    current_user: CurrentUser,
    service: Annotated[ProdutoService, Depends(get_produto_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=150),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    categoria_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
) -> ListaProdutosResposta:
    items, total = await service.list(
        current_user.empresa_id,
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
        categoria_id=categoria_id,
        is_active=is_active,
    )
    return ListaProdutosResposta(
        items=[ProdutoResposta.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{produto_id}",
    response_model=ProdutoResposta,
    dependencies=[
        Depends(require_permissions("produto.ler")),
    ],
)
async def get_produto(
    produto_id: int,
    current_user: CurrentUser,
    service: Annotated[ProdutoService, Depends(get_produto_service)],
) -> ProdutoResposta:
    produto = await service.get_by_id(produto_id, current_user.empresa_id)
    return ProdutoResposta.model_validate(produto)


@router.post(
    "",
    response_model=ProdutoResposta,
    status_code=201,
    dependencies=[
        Depends(require_permissions("produto.criar")),
    ],
)
async def create_produto(
    data: ProdutoCriarPayload,
    current_user: CurrentUser,
    service: Annotated[ProdutoService, Depends(get_produto_service)],
) -> ProdutoResposta:
    produto = await service.create(
        current_user.empresa_id, data, user_id=current_user.id
    )
    return ProdutoResposta.model_validate(produto)


@router.patch(
    "/{produto_id}",
    response_model=ProdutoResposta,
    dependencies=[
        Depends(require_permissions("produto.atualizar")),
    ],
)
async def update_produto(
    produto_id: int,
    data: ProdutoAtualizarPayload,
    current_user: CurrentUser,
    service: Annotated[ProdutoService, Depends(get_produto_service)],
) -> ProdutoResposta:
    produto = await service.update(
        produto_id, current_user.empresa_id, data, user_id=current_user.id
    )
    return ProdutoResposta.model_validate(produto)


@router.delete(
    "/{produto_id}",
    status_code=204,
    dependencies=[
        Depends(require_permissions("produto.excluir")),
    ],
)
async def delete_produto(
    produto_id: int,
    current_user: CurrentUser,
    service: Annotated[ProdutoService, Depends(get_produto_service)],
) -> None:
    await service.soft_delete(
        produto_id, current_user.empresa_id, user_id=current_user.id
    )
