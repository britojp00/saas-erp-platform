from asyncpg import UniqueViolationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ErroClienteDuplicado, ErroClienteNaoEncontrado
from app.db.models.cliente import Cliente
from app.repositories.cliente import ClienteRepository
from app.schemas.cliente import ClienteAtualizarPayload, ClienteCriarPayload
from app.services.audit_log import AuditLogService


class ClienteService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ClienteRepository(session)
        self.audit_service = AuditLogService(session)

    async def list(
        self,
        empresa_id: int,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[Cliente], int]:
        offset = (page - 1) * page_size
        return await self.repo.list(
            empresa_id,
            offset=offset,
            limit=page_size,
            search=search,
            sort=sort,
            order=order,
        )

    async def get_by_id(
        self,
        cliente_id: int,
        empresa_id: int,
    ) -> Cliente:
        cliente = await self.repo.get_by_id(cliente_id, empresa_id)
        if cliente is None:
            raise ErroClienteNaoEncontrado()
        return cliente

    async def create(
        self,
        empresa_id: int,
        data: ClienteCriarPayload,
        user_id: int | None = None,
    ) -> Cliente:
        if data.document:
            exists = await self.repo.exists_by_document(empresa_id, data.document)
            if exists:
                raise ErroClienteDuplicado()

        cliente = Cliente(
            empresa_id=empresa_id,
            name=data.name.strip(),
            document=data.document,
            email=data.email,
            phone=data.phone,
            notes=data.notes,
        )

        try:
            result = await self.repo.create(cliente)
        except UniqueViolationError:
            raise ErroClienteDuplicado()

        await self.audit_service.log(
            empresa_id=empresa_id,
            user_id=user_id,
            action="CLIENTE_CRIAR",
            entity_type="cliente",
            entity_id=result.id,
            new_values={
                "name": result.name,
                "document": result.document,
                "email": result.email,
                "phone": result.phone,
            },
        )

        return result

    async def update(
        self,
        cliente_id: int,
        empresa_id: int,
        data: ClienteAtualizarPayload,
        user_id: int | None = None,
    ) -> Cliente:
        cliente = await self.repo.get_by_id(cliente_id, empresa_id)
        if cliente is None:
            raise ErroClienteNaoEncontrado()

        old_values = {
            "name": cliente.name,
            "document": cliente.document,
            "email": cliente.email,
            "phone": cliente.phone,
        }

        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data:
            cliente.name = update_data["name"].strip()
        if "document" in update_data:
            new_document = update_data["document"]
            if new_document is not None and new_document != cliente.document:
                exists = await self.repo.exists_by_document(
                    empresa_id, new_document, exclude_id=cliente.id
                )
                if exists:
                    raise ErroClienteDuplicado()
            cliente.document = new_document
        if "email" in update_data:
            cliente.email = update_data["email"]
        if "phone" in update_data:
            cliente.phone = update_data["phone"]
        if "notes" in update_data:
            cliente.notes = update_data["notes"]

        try:
            result = await self.repo.update(cliente)
        except UniqueViolationError:
            raise ErroClienteDuplicado()

        new_values = {
            "name": result.name,
            "document": result.document,
            "email": result.email,
            "phone": result.phone,
        }

        await self.audit_service.log(
            empresa_id=empresa_id,
            user_id=user_id,
            action="CLIENTE_ATUALIZAR",
            entity_type="cliente",
            entity_id=result.id,
            old_values=old_values,
            new_values=new_values,
        )

        return result

    async def soft_delete(
        self,
        cliente_id: int,
        empresa_id: int,
        user_id: int | None = None,
    ) -> None:
        cliente = await self.repo.get_by_id(cliente_id, empresa_id)
        if cliente is None:
            raise ErroClienteNaoEncontrado()

        old_values = {
            "name": cliente.name,
            "document": cliente.document,
        }

        await self.repo.soft_delete(cliente)

        await self.audit_service.log(
            empresa_id=empresa_id,
            user_id=user_id,
            action="CLIENTE_EXCLUIR",
            entity_type="cliente",
            entity_id=cliente_id,
            old_values=old_values,
        )
