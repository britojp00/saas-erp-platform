from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ErroEstadoPedidoInvalido,
    ErroItemPedidoDuplicado,
    ErroItemPedidoNaoEncontrado,
    ErroPedidoClienteNaoEncontrado,
    ErroPedidoNaoEncontrado,
    ErroPedidoProdutoInativo,
    ErroPedidoProdutoNaoEncontrado,
    ErroPedidoSemItens,
    ErroRemocaoItemPedidoNaoPermitida,
)
from app.db.models.cliente import Cliente
from app.db.models.pedido import Pedido, StatusPedido
from app.db.models.pedido_item import PedidoItem
from app.db.models.produto import Produto
from app.db.models.reserva_estoque import ReservaEstoque, StatusReserva
from app.repositories.cliente import ClienteRepository
from app.repositories.estoque import EstoqueRepository
from app.repositories.pedido import PedidoRepository
from app.repositories.pedido_item import PedidoItemRepository
from app.repositories.produto import ProdutoRepository
from app.repositories.reserva_estoque import ReservaEstoqueRepository
from app.schemas.pedido import (
    PedidoAtualizarPayload,
    PedidoCriarPayload,
    PedidoItemAtualizarPayload,
    PedidoItemCriarPayload,
)
from app.services.audit_log import AuditLogService

VALID_TRANSITIONS: dict[str, list[str]] = {
    StatusPedido.RASCUNHO: [StatusPedido.CONFIRMADO, StatusPedido.CANCELADO],
    StatusPedido.CONFIRMADO: [StatusPedido.CONCLUIDO, StatusPedido.CANCELADO],
}


class PedidoService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pedido_repo = PedidoRepository(session)
        self.item_repo = PedidoItemRepository(session)
        self.produto_repo = ProdutoRepository(session)
        self.cliente_repo = ClienteRepository(session)
        self.estoque_repo = EstoqueRepository(session)
        self.reserva_repo = ReservaEstoqueRepository(session)
        self.audit_service = AuditLogService(session)

    async def listar_pedidos(
        self,
        empresa_id: int,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
        status: str | None = None,
        cliente_id: int | None = None,
    ) -> tuple[list[Pedido], int]:
        offset = (page - 1) * page_size
        return await self.pedido_repo.list(
            empresa_id,
            offset=offset,
            limit=page_size,
            search=search,
            sort=sort,
            order=order,
            status=status,
            cliente_id=cliente_id,
        )

    async def obter_pedido(
        self,
        empresa_id: int,
        pedido_id: int,
    ) -> Pedido:
        pedido = await self.pedido_repo.get_by_id(empresa_id, pedido_id)
        if pedido is None:
            raise ErroPedidoNaoEncontrado()
        return pedido

    async def obter_pedido_com_itens(
        self,
        empresa_id: int,
        pedido_id: int,
    ) -> Pedido:
        pedido = await self.obter_pedido(empresa_id, pedido_id)
        pedido.itens = await self.item_repo.listar_por_pedido(empresa_id, pedido_id)
        return pedido

    async def _validar_cliente(
        self,
        empresa_id: int,
        cliente_id: int,
    ) -> Cliente:
        cliente = await self.cliente_repo.get_by_id(cliente_id, empresa_id)
        if cliente is None:
            raise ErroPedidoClienteNaoEncontrado()
        return cliente

    async def _validar_produto(
        self,
        empresa_id: int,
        produto_id: int,
    ) -> Produto:
        produto = await self.produto_repo.get_by_id(produto_id, empresa_id)
        if produto is None:
            raise ErroPedidoProdutoNaoEncontrado()
        return produto

    async def _recalcular_total(self, pedido: Pedido) -> None:
        items = await self.item_repo.listar_por_pedido(pedido.empresa_id, pedido.id)
        pedido.total_amount = sum(item.total_price for item in items)

    async def criar_pedido(
        self,
        empresa_id: int,
        data: PedidoCriarPayload,
        user_id: int | None = None,
    ) -> Pedido:
        await self._validar_cliente(empresa_id, data.cliente_id)

        produto_ids = [item.produto_id for item in data.itens]
        if len(produto_ids) != len(set(produto_ids)):
            raise ErroItemPedidoDuplicado()

        numero_pedido = await self.pedido_repo.proximo_numero_pedido(empresa_id)

        pedido = Pedido(
            empresa_id=empresa_id,
            numero_pedido=numero_pedido,
            cliente_id=data.cliente_id,
            notes=data.notes,
        )
        await self.pedido_repo.create(pedido)

        for item_data in data.itens:
            produto = await self._validar_produto(empresa_id, item_data.produto_id)

            unit_price = (
                item_data.unit_price
                if item_data.unit_price is not None
                else produto.price
            )
            total_price = unit_price * item_data.quantity

            item = PedidoItem(
                empresa_id=empresa_id,
                pedido_id=pedido.id,
                produto_id=produto.id,
                quantity=item_data.quantity,
                unit_price=unit_price,
                total_price=total_price,
            )
            await self.item_repo.create(item)

        await self._recalcular_total(pedido)
        await self.pedido_repo.update(pedido)

        await self.audit_service.log(
            empresa_id=empresa_id,
            user_id=user_id,
            action="PEDIDO_CRIAR",
            entity_type="pedido",
            entity_id=pedido.id,
            new_values={
                "numero_pedido": pedido.numero_pedido,
                "cliente_id": pedido.cliente_id,
                "status": pedido.status,
            },
        )

        return pedido

    async def atualizar_pedido(
        self,
        empresa_id: int,
        pedido_id: int,
        data: PedidoAtualizarPayload,
        user_id: int | None = None,
    ) -> Pedido:
        pedido = await self.pedido_repo.get_for_update(empresa_id, pedido_id)
        if pedido is None:
            raise ErroPedidoNaoEncontrado()

        if pedido.status != StatusPedido.RASCUNHO:
            raise ErroEstadoPedidoInvalido()

        old_values = {
            "cliente_id": pedido.cliente_id,
            "notes": pedido.notes,
        }

        update_data = data.model_dump(exclude_unset=True)

        if "cliente_id" in update_data and update_data["cliente_id"] is not None:
            await self._validar_cliente(empresa_id, update_data["cliente_id"])
            pedido.cliente_id = update_data["cliente_id"]

        if "notes" in update_data:
            pedido.notes = update_data["notes"]

        result = await self.pedido_repo.update(pedido)

        new_values = {
            "cliente_id": result.cliente_id,
            "notes": result.notes,
        }

        await self.audit_service.log(
            empresa_id=empresa_id,
            user_id=user_id,
            action="PEDIDO_ATUALIZAR",
            entity_type="pedido",
            entity_id=pedido_id,
            old_values=old_values,
            new_values=new_values,
        )

        return result

    async def adicionar_item(
        self,
        empresa_id: int,
        pedido_id: int,
        data: PedidoItemCriarPayload,
        user_id: int | None = None,
    ) -> PedidoItem:
        pedido = await self.pedido_repo.get_for_update(empresa_id, pedido_id)
        if pedido is None:
            raise ErroPedidoNaoEncontrado()

        if pedido.status != StatusPedido.RASCUNHO:
            raise ErroEstadoPedidoInvalido()

        if await self.item_repo.existe_produto_no_pedido(
            empresa_id, pedido_id, data.produto_id
        ):
            raise ErroItemPedidoDuplicado()

        produto = await self._validar_produto(empresa_id, data.produto_id)

        unit_price = data.unit_price if data.unit_price is not None else produto.price
        total_price = unit_price * data.quantity

        item = PedidoItem(
            empresa_id=empresa_id,
            pedido_id=pedido_id,
            produto_id=produto.id,
            quantity=data.quantity,
            unit_price=unit_price,
            total_price=total_price,
        )
        await self.item_repo.create(item)

        await self._recalcular_total(pedido)
        await self.pedido_repo.update(pedido)

        await self.audit_service.log(
            empresa_id=empresa_id,
            user_id=user_id,
            action="PEDIDO_ITEM_ADICIONAR",
            entity_type="pedido_item",
            entity_id=item.id,
            new_values={
                "pedido_id": pedido_id,
                "produto_id": produto.id,
                "quantity": str(data.quantity),
                "unit_price": str(unit_price),
            },
        )

        return item

    async def atualizar_item(
        self,
        empresa_id: int,
        pedido_id: int,
        item_id: int,
        data: PedidoItemAtualizarPayload,
        user_id: int | None = None,
    ) -> PedidoItem:
        pedido = await self.pedido_repo.get_for_update(empresa_id, pedido_id)
        if pedido is None:
            raise ErroPedidoNaoEncontrado()

        if pedido.status != StatusPedido.RASCUNHO:
            raise ErroEstadoPedidoInvalido()

        item = await self.item_repo.obter_por_id_e_pedido(
            empresa_id, item_id, pedido_id
        )
        if item is None:
            raise ErroItemPedidoNaoEncontrado()

        old_values = {
            "quantity": str(item.quantity),
            "unit_price": str(item.unit_price),
        }

        update_data = data.model_dump(exclude_unset=True)

        if "quantity" in update_data and update_data["quantity"] is not None:
            item.quantity = update_data["quantity"]
            item.total_price = item.unit_price * item.quantity

        if "unit_price" in update_data and update_data["unit_price"] is not None:
            item.unit_price = update_data["unit_price"]
            item.total_price = item.unit_price * item.quantity

        await self.item_repo.update(item)

        await self._recalcular_total(pedido)
        await self.pedido_repo.update(pedido)

        new_values = {
            "quantity": str(item.quantity),
            "unit_price": str(item.unit_price),
        }

        await self.audit_service.log(
            empresa_id=empresa_id,
            user_id=user_id,
            action="PEDIDO_ITEM_ATUALIZAR",
            entity_type="pedido_item",
            entity_id=item_id,
            old_values=old_values,
            new_values=new_values,
        )

        return item

    async def remover_item(
        self,
        empresa_id: int,
        pedido_id: int,
        item_id: int,
        user_id: int | None = None,
    ) -> None:
        pedido = await self.pedido_repo.get_for_update(empresa_id, pedido_id)
        if pedido is None:
            raise ErroPedidoNaoEncontrado()

        if pedido.status != StatusPedido.RASCUNHO:
            raise ErroEstadoPedidoInvalido()

        item = await self.item_repo.obter_por_id_e_pedido(
            empresa_id, item_id, pedido_id
        )
        if item is None:
            raise ErroItemPedidoNaoEncontrado()

        count = await self.item_repo.contar_por_pedido(empresa_id, pedido_id)
        if count <= 1:
            raise ErroRemocaoItemPedidoNaoPermitida()

        old_values = {
            "produto_id": item.produto_id,
            "quantity": str(item.quantity),
            "unit_price": str(item.unit_price),
        }

        await self.item_repo.delete(item)

        await self._recalcular_total(pedido)
        await self.pedido_repo.update(pedido)

        await self.audit_service.log(
            empresa_id=empresa_id,
            user_id=user_id,
            action="PEDIDO_ITEM_REMOVER",
            entity_type="pedido_item",
            entity_id=item_id,
            old_values=old_values,
        )

    async def confirmar_pedido(
        self,
        empresa_id: int,
        pedido_id: int,
        user_id: int | None = None,
    ) -> Pedido:
        pedido = await self.pedido_repo.get_for_update(empresa_id, pedido_id)
        if pedido is None:
            raise ErroPedidoNaoEncontrado()

        if pedido.status != StatusPedido.RASCUNHO:
            raise ErroEstadoPedidoInvalido()

        items = await self.item_repo.listar_por_pedido(empresa_id, pedido_id)
        if not items:
            raise ErroPedidoSemItens()

        for item in items:
            produto = await self.produto_repo.get_by_id(item.produto_id, empresa_id)
            if (
                produto is None
                or not produto.is_active
                or produto.deleted_at is not None
            ):
                raise ErroPedidoProdutoInativo()

            estoque = await self.estoque_repo.get_for_update(
                empresa_id, item.produto_id
            )
            if estoque is None:
                raise ErroPedidoProdutoInativo()

            available = estoque.quantity - estoque.reserved_quantity
            if available < item.quantity:
                raise ErroPedidoProdutoInativo()

            estoque.reserved_quantity = estoque.reserved_quantity + item.quantity

            reserva = ReservaEstoque(
                empresa_id=empresa_id,
                produto_id=item.produto_id,
                quantity=item.quantity,
                status=StatusReserva.ATIVA,
                reference=f"pedido:{pedido.id}",
                pedido_item_id=item.id,
                idempotency_key=f"pedido:{pedido.id}:item:{item.id}",
            )
            await self.reserva_repo.create(reserva)

        old_status = pedido.status
        pedido.status = StatusPedido.CONFIRMADO
        pedido.updated_at = datetime.now(UTC)

        result = await self.pedido_repo.update(pedido)

        await self.audit_service.log(
            empresa_id=empresa_id,
            user_id=user_id,
            action="PEDIDO_CONFIRMAR",
            entity_type="pedido",
            entity_id=pedido_id,
            old_values={"status": old_status},
            new_values={"status": "CONFIRMADO"},
        )

        return result

    async def cancelar_pedido(
        self,
        empresa_id: int,
        pedido_id: int,
        user_id: int | None = None,
    ) -> Pedido:
        pedido = await self.pedido_repo.get_for_update(empresa_id, pedido_id)
        if pedido is None:
            raise ErroPedidoNaoEncontrado()

        if pedido.status not in VALID_TRANSITIONS:
            raise ErroEstadoPedidoInvalido()

        reference = f"pedido:{pedido.id}"
        reservas = await self.reserva_repo.list_active_by_reference(
            empresa_id, reference
        )
        for reserva in reservas:
            estoque = await self.estoque_repo.get_for_update(
                empresa_id, reserva.produto_id
            )
            if estoque is not None:
                estoque.reserved_quantity = estoque.reserved_quantity - reserva.quantity

            reserva.status = StatusReserva.CANCELADA
            reserva.released_at = datetime.now(UTC)
            await self.reserva_repo.update(reserva)

        old_status = pedido.status
        pedido.status = StatusPedido.CANCELADO
        pedido.updated_at = datetime.now(UTC)

        result = await self.pedido_repo.update(pedido)

        await self.audit_service.log(
            empresa_id=empresa_id,
            user_id=user_id,
            action="PEDIDO_CANCELAR",
            entity_type="pedido",
            entity_id=pedido_id,
            old_values={"status": old_status},
            new_values={"status": "CANCELADO"},
        )

        return result

    async def concluir_pedido(
        self,
        empresa_id: int,
        pedido_id: int,
        user_id: int | None = None,
    ) -> Pedido:
        pedido = await self.pedido_repo.get_for_update(empresa_id, pedido_id)
        if pedido is None:
            raise ErroPedidoNaoEncontrado()

        if pedido.status != StatusPedido.CONFIRMADO:
            raise ErroEstadoPedidoInvalido()

        reference = f"pedido:{pedido.id}"
        reservas = await self.reserva_repo.list_active_by_reference(
            empresa_id, reference
        )
        for reserva in reservas:
            estoque = await self.estoque_repo.get_for_update(
                empresa_id, reserva.produto_id
            )
            if estoque is not None:
                estoque.quantity = estoque.quantity - reserva.quantity
                estoque.reserved_quantity = estoque.reserved_quantity - reserva.quantity

            reserva.status = StatusReserva.CONFIRMADA
            reserva.confirmed_at = datetime.now(UTC)
            await self.reserva_repo.update(reserva)

        old_status = pedido.status
        pedido.status = StatusPedido.CONCLUIDO
        pedido.updated_at = datetime.now(UTC)

        result = await self.pedido_repo.update(pedido)

        await self.audit_service.log(
            empresa_id=empresa_id,
            user_id=user_id,
            action="PEDIDO_CONCLUIR",
            entity_type="pedido",
            entity_id=pedido_id,
            old_values={"status": old_status},
            new_values={"status": "CONCLUIDO"},
        )

        return result
