from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.categoria import Categoria
from app.db.models.produto import Produto

SORT_FIELDS = {
    "name": Categoria.name,
    "created_at": Categoria.created_at,
}


class CategoriaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        empresa_id: int,
        *,
        offset: int,
        limit: int,
        search: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[Categoria], int]:
        base_stmt = select(Categoria).where(
            Categoria.empresa_id == empresa_id,
            Categoria.deleted_at.is_(None),
        )
        if search:
            base_stmt = base_stmt.where(Categoria.name.ilike(f"%{search}%"))

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        sort_column = SORT_FIELDS.get(sort, Categoria.created_at)
        if order == "asc":
            base_stmt = base_stmt.order_by(sort_column.asc(), Categoria.id.asc())
        else:
            base_stmt = base_stmt.order_by(sort_column.desc(), Categoria.id.desc())

        base_stmt = base_stmt.offset(offset).limit(limit)
        result = await self.session.execute(base_stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_by_id(
        self,
        categoria_id: int,
        empresa_id: int,
    ) -> Categoria | None:
        stmt = select(Categoria).where(
            Categoria.id == categoria_id,
            Categoria.empresa_id == empresa_id,
            Categoria.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_name(
        self,
        empresa_id: int,
        name: str,
        exclude_id: int | None = None,
    ) -> bool:
        stmt = select(Categoria).where(
            Categoria.empresa_id == empresa_id,
            Categoria.name == name,
        )
        if exclude_id is not None:
            stmt = stmt.where(Categoria.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_children_ids(
        self,
        empresa_id: int,
        parent_id: int,
    ) -> set[int]:
        stmt = select(Categoria.id).where(
            Categoria.empresa_id == empresa_id,
            Categoria.parent_id == parent_id,
            Categoria.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())

    async def get_ancestor_ids(
        self,
        empresa_id: int,
        categoria_id: int,
    ) -> set[int]:
        ancestors: set[int] = set()
        current_parent_id = categoria_id
        while True:
            stmt = select(Categoria.parent_id).where(
                Categoria.id == current_parent_id,
                Categoria.empresa_id == empresa_id,
                Categoria.deleted_at.is_(None),
            )
            result = await self.session.execute(stmt)
            parent_id = result.scalar_one_or_none()
            if parent_id is None:
                break
            if parent_id in ancestors:
                break
            ancestors.add(parent_id)
            current_parent_id = parent_id
        return ancestors

    async def has_children(
        self,
        empresa_id: int,
        categoria_id: int,
    ) -> bool:
        children = await self.get_children_ids(empresa_id, categoria_id)
        return len(children) > 0

    async def has_produtos(
        self,
        empresa_id: int,
        categoria_id: int,
    ) -> bool:
        stmt = (
            select(Produto)
            .where(
                Produto.empresa_id == empresa_id,
                Produto.categoria_id == categoria_id,
                Produto.deleted_at.is_(None),
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, categoria: Categoria) -> Categoria:
        self.session.add(categoria)
        await self.session.flush()
        return categoria

    async def update(self, categoria: Categoria) -> Categoria:
        await self.session.flush()
        await self.session.refresh(categoria)
        return categoria

    async def soft_delete(self, categoria: Categoria) -> None:
        categoria.deleted_at = datetime.now(UTC)
        await self.session.flush()
