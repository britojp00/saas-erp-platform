from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ErroProdutoCategoriaInvalida,
    ErroProdutoDuplicado,
    ErroProdutoEmUso,
    ErroProdutoNaoEncontrado,
)
from app.db.models.produto import Produto
from app.repositories.produto import ProdutoRepository
from app.schemas.produto import ProdutoAtualizarPayload, ProdutoCriarPayload
from app.services.audit_log import AuditLogService


class ProdutoService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProdutoRepository(session)
        self.audit_service = AuditLogService(session)

    async def _validate_categoria(
        self,
        tenant_id: int,
        categoria_id: int | None,
    ) -> None:
        if categoria_id is None:
            return
        categoria = await self.repo.get_categoria_by_id(categoria_id, tenant_id)
        if categoria is None:
            raise ErroProdutoCategoriaInvalida()

    async def list(
        self,
        tenant_id: int,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
        categoria_id: int | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Produto], int]:
        offset = (page - 1) * page_size
        return await self.repo.list(
            tenant_id,
            offset=offset,
            limit=page_size,
            search=search,
            sort=sort,
            order=order,
            categoria_id=categoria_id,
            is_active=is_active,
        )

    async def get_by_id(
        self,
        produto_id: int,
        tenant_id: int,
    ) -> Produto:
        produto = await self.repo.get_by_id(produto_id, tenant_id)
        if produto is None:
            raise ErroProdutoNaoEncontrado()
        return produto

    async def create(
        self,
        tenant_id: int,
        data: ProdutoCriarPayload,
        user_id: int | None = None,
    ) -> Produto:
        await self._validate_categoria(tenant_id, data.categoria_id)

        if await self.repo.exists_by_sku(tenant_id, data.sku.strip()):
            raise ErroProdutoDuplicado()

        produto = Produto(
            tenant_id=tenant_id,
            sku=data.sku.strip(),
            name=data.name.strip(),
            description=data.description,
            categoria_id=data.categoria_id,
            price=data.price,
            cost_price=data.cost_price,
            is_active=data.is_active,
        )

        try:
            result = await self.repo.create(produto)
        except IntegrityError:
            raise ErroProdutoDuplicado()

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="PRODUTO_CRIAR",
            entity_type="produto",
            entity_id=result.id,
            new_values={
                "sku": result.sku,
                "name": result.name,
                "price": str(result.price),
                "is_active": result.is_active,
            },
        )

        return result

    async def update(
        self,
        produto_id: int,
        tenant_id: int,
        data: ProdutoAtualizarPayload,
        user_id: int | None = None,
    ) -> Produto:
        produto = await self.repo.get_by_id(produto_id, tenant_id)
        if produto is None:
            raise ErroProdutoNaoEncontrado()

        old_values = {
            "sku": produto.sku,
            "name": produto.name,
            "price": str(produto.price),
            "is_active": produto.is_active,
        }

        update_data = data.model_dump(exclude_unset=True)

        if "categoria_id" in update_data:
            new_categoria_id = update_data["categoria_id"]
            if new_categoria_id is not None:
                await self._validate_categoria(tenant_id, new_categoria_id)
            produto.categoria_id = new_categoria_id

        if "sku" in update_data:
            new_sku = update_data["sku"].strip()
            if new_sku != produto.sku and await self.repo.exists_by_sku(
                tenant_id, new_sku, exclude_id=produto.id
            ):
                raise ErroProdutoDuplicado()
            produto.sku = new_sku

        if "name" in update_data:
            produto.name = update_data["name"].strip()
        if "description" in update_data:
            produto.description = update_data["description"]
        if "price" in update_data:
            produto.price = update_data["price"]
        if "cost_price" in update_data:
            produto.cost_price = update_data["cost_price"]
        if "is_active" in update_data:
            produto.is_active = update_data["is_active"]

        try:
            result = await self.repo.update(produto)
        except IntegrityError:
            raise ErroProdutoDuplicado()

        new_values = {
            "sku": result.sku,
            "name": result.name,
            "price": str(result.price),
            "is_active": result.is_active,
        }

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="PRODUTO_ATUALIZAR",
            entity_type="produto",
            entity_id=result.id,
            old_values=old_values,
            new_values=new_values,
        )

        return result

    async def soft_delete(
        self,
        produto_id: int,
        tenant_id: int,
        user_id: int | None = None,
    ) -> None:
        produto = await self.repo.get_by_id(produto_id, tenant_id)
        if produto is None:
            raise ErroProdutoNaoEncontrado()

        if await self.repo.has_inventory(tenant_id, produto.id):
            raise ErroProdutoEmUso()

        if await self.repo.has_order_items(tenant_id, produto.id):
            raise ErroProdutoEmUso()

        old_values = {
            "sku": produto.sku,
            "name": produto.name,
        }

        await self.repo.soft_delete(produto)

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="PRODUTO_EXCLUIR",
            entity_type="produto",
            entity_id=produto_id,
            old_values=old_values,
        )
