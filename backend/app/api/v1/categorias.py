from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_permissions
from app.db.database import get_db_session
from app.schemas.categoria import (
    CategoriaAtualizarPayload,
    CategoriaCriarPayload,
    CategoriaResposta,
    ListaCategoriasResposta,
)
from app.services.categoria import CategoriaService

router = APIRouter(prefix="/categorias", tags=["Categorias"])


async def get_categoria_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CategoriaService:
    return CategoriaService(db)


@router.get(
    "",
    response_model=ListaCategoriasResposta,
    dependencies=[
        Depends(require_permissions("categoria.ler")),
    ],
)
async def list_categorias(
    current_user: CurrentUser,
    service: Annotated[CategoriaService, Depends(get_categoria_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=100),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
) -> ListaCategoriasResposta:
    items, total = await service.list(
        current_user.tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
        order=order,
    )
    return ListaCategoriasResposta(
        items=[CategoriaResposta.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{categoria_id}",
    response_model=CategoriaResposta,
    dependencies=[
        Depends(require_permissions("categoria.ler")),
    ],
)
async def get_categoria(
    categoria_id: int,
    current_user: CurrentUser,
    service: Annotated[CategoriaService, Depends(get_categoria_service)],
) -> CategoriaResposta:
    categoria = await service.get_by_id(categoria_id, current_user.tenant_id)
    return CategoriaResposta.model_validate(categoria)


@router.post(
    "",
    response_model=CategoriaResposta,
    status_code=201,
    dependencies=[
        Depends(require_permissions("categoria.criar")),
    ],
)
async def create_categoria(
    data: CategoriaCriarPayload,
    current_user: CurrentUser,
    service: Annotated[CategoriaService, Depends(get_categoria_service)],
) -> CategoriaResposta:
    categoria = await service.create(
        current_user.tenant_id, data, user_id=current_user.id
    )
    return CategoriaResposta.model_validate(categoria)


@router.patch(
    "/{categoria_id}",
    response_model=CategoriaResposta,
    dependencies=[
        Depends(require_permissions("categoria.atualizar")),
    ],
)
async def update_categoria(
    categoria_id: int,
    data: CategoriaAtualizarPayload,
    current_user: CurrentUser,
    service: Annotated[CategoriaService, Depends(get_categoria_service)],
) -> CategoriaResposta:
    categoria = await service.update(
        categoria_id, current_user.tenant_id, data, user_id=current_user.id
    )
    return CategoriaResposta.model_validate(categoria)


@router.delete(
    "/{categoria_id}",
    status_code=204,
    dependencies=[
        Depends(require_permissions("categoria.excluir")),
    ],
)
async def delete_categoria(
    categoria_id: int,
    current_user: CurrentUser,
    service: Annotated[CategoriaService, Depends(get_categoria_service)],
) -> None:
    await service.soft_delete(
        categoria_id, current_user.tenant_id, user_id=current_user.id
    )
