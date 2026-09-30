from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ErroCategoriaAutorreferencia,
    ErroCategoriaCicloDetectado,
    ErroCategoriaDuplicada,
    ErroCategoriaNaoEncontrada,
    ErroCategoriaPaiNaoEncontrada,
    ErroCategoriaPossuiFilhos,
    ErroCategoriaPossuiProdutos,
)
from app.db.models.categoria import Categoria
from app.repositories.categoria import CategoriaRepository
from app.schemas.categoria import CategoriaAtualizarPayload, CategoriaCriarPayload
from app.services.audit_log import AuditLogService


class CategoriaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CategoriaRepository(session)
        self.audit_service = AuditLogService(session)

    async def list(
        self,
        tenant_id: int,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[Categoria], int]:
        offset = (page - 1) * page_size
        return await self.repo.list(
            tenant_id,
            offset=offset,
            limit=page_size,
            search=search,
            sort=sort,
            order=order,
        )

    async def get_by_id(
        self,
        categoria_id: int,
        tenant_id: int,
    ) -> Categoria:
        categoria = await self.repo.get_by_id(categoria_id, tenant_id)
        if categoria is None:
            raise ErroCategoriaNaoEncontrada()
        return categoria

    async def _validate_parent(
        self,
        tenant_id: int,
        parent_id: int | None,
        exclude_id: int | None = None,
    ) -> None:
        if parent_id is None:
            return

        if parent_id == exclude_id:
            raise ErroCategoriaAutorreferencia()

        parent = await self.repo.get_by_id(parent_id, tenant_id)
        if parent is None:
            raise ErroCategoriaPaiNaoEncontrada()

        if exclude_id is not None:
            ancestors = await self.repo.get_ancestor_ids(tenant_id, parent_id)
            if exclude_id in ancestors:
                raise ErroCategoriaCicloDetectado()

    async def create(
        self,
        tenant_id: int,
        data: CategoriaCriarPayload,
        user_id: int | None = None,
    ) -> Categoria:
        if data.parent_id is not None:
            await self._validate_parent(tenant_id, data.parent_id)

        if await self.repo.exists_by_name(tenant_id, data.name.strip()):
            raise ErroCategoriaDuplicada()

        categoria = Categoria(
            tenant_id=tenant_id,
            name=data.name.strip(),
            description=data.description,
            parent_id=data.parent_id,
        )

        try:
            result = await self.repo.create(categoria)
        except IntegrityError:
            raise ErroCategoriaDuplicada()

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="CATEGORIA_CRIAR",
            entity_type="categoria",
            entity_id=result.id,
            new_values={
                "name": result.name,
                "description": result.description,
                "parent_id": result.parent_id,
            },
        )

        return result

    async def update(
        self,
        categoria_id: int,
        tenant_id: int,
        data: CategoriaAtualizarPayload,
        user_id: int | None = None,
    ) -> Categoria:
        categoria = await self.repo.get_by_id(categoria_id, tenant_id)
        if categoria is None:
            raise ErroCategoriaNaoEncontrada()

        old_values = {
            "name": categoria.name,
            "description": categoria.description,
            "parent_id": categoria.parent_id,
        }

        update_data = data.model_dump(exclude_unset=True)

        if "parent_id" in update_data:
            new_parent_id = update_data["parent_id"]
            await self._validate_parent(
                tenant_id, new_parent_id, exclude_id=categoria.id
            )
            categoria.parent_id = new_parent_id

        if "name" in update_data:
            new_name = update_data["name"].strip()
            if new_name != categoria.name and await self.repo.exists_by_name(
                tenant_id, new_name, exclude_id=categoria.id
            ):
                raise ErroCategoriaDuplicada()
            categoria.name = new_name
        if "description" in update_data:
            categoria.description = update_data["description"]

        try:
            result = await self.repo.update(categoria)
        except IntegrityError:
            raise ErroCategoriaDuplicada()

        new_values = {
            "name": result.name,
            "description": result.description,
            "parent_id": result.parent_id,
        }

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="CATEGORIA_ATUALIZAR",
            entity_type="categoria",
            entity_id=result.id,
            old_values=old_values,
            new_values=new_values,
        )

        return result

    async def soft_delete(
        self,
        categoria_id: int,
        tenant_id: int,
        user_id: int | None = None,
    ) -> None:
        categoria = await self.repo.get_by_id(categoria_id, tenant_id)
        if categoria is None:
            raise ErroCategoriaNaoEncontrada()

        if await self.repo.has_children(tenant_id, categoria.id):
            raise ErroCategoriaPossuiFilhos()

        if await self.repo.has_products(tenant_id, categoria.id):
            raise ErroCategoriaPossuiProdutos()

        old_values = {
            "name": categoria.name,
            "description": categoria.description,
        }

        await self.repo.soft_delete(categoria)

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="CATEGORIA_EXCLUIR",
            entity_type="categoria",
            entity_id=categoria_id,
            old_values=old_values,
        )
