from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DuplicateOrderItemError,
    ErroPedidoClienteNaoEncontrado,
    ErroPedidoProdutoInativo,
    ErroPedidoProdutoNaoEncontrado,
    InvalidOrderStateError,
    OrderItemNotFoundError,
    OrderItemRemovalNotAllowedError,
    OrderMustHaveItemsError,
    OrderNotFoundError,
)
from app.db.models.cliente import Cliente
from app.db.models.inventory_reservation import InventoryReservation, ReservationStatus
from app.db.models.order import Order
from app.db.models.order_item import OrderItem
from app.db.models.produto import Produto
from app.repositories.cliente import ClienteRepository
from app.repositories.inventory import InventoryRepository
from app.repositories.inventory_reservation import InventoryReservationRepository
from app.repositories.order import OrderRepository
from app.repositories.order_item import OrderItemRepository
from app.repositories.produto import ProdutoRepository
from app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
    OrderItemUpdate,
    OrderUpdate,
)
from app.services.audit_log import AuditLogService

VALID_TRANSITIONS: dict[str, list[str]] = {
    "DRAFT": ["CONFIRMED", "CANCELLED"],
    "CONFIRMED": ["COMPLETED", "CANCELLED"],
}


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.order_repo = OrderRepository(session)
        self.item_repo = OrderItemRepository(session)
        self.produto_repo = ProdutoRepository(session)
        self.cliente_repo = ClienteRepository(session)
        self.inventory_repo = InventoryRepository(session)
        self.reservation_repo = InventoryReservationRepository(session)
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
        status: str | None = None,
        cliente_id: int | None = None,
    ) -> tuple[list[Order], int]:
        offset = (page - 1) * page_size
        return await self.order_repo.list(
            tenant_id,
            offset=offset,
            limit=page_size,
            search=search,
            sort=sort,
            order=order,
            status=status,
            cliente_id=cliente_id,
        )

    async def get_by_id(
        self,
        tenant_id: int,
        order_id: int,
    ) -> Order:
        order = await self.order_repo.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFoundError()
        return order

    async def get_with_items(
        self,
        tenant_id: int,
        order_id: int,
    ) -> Order:
        order = await self.get_by_id(tenant_id, order_id)
        order.items = await self.item_repo.list_by_order(tenant_id, order_id)
        return order

    async def _validate_cliente(
        self,
        tenant_id: int,
        cliente_id: int,
    ) -> Cliente:
        cliente = await self.cliente_repo.get_by_id(cliente_id, tenant_id)
        if cliente is None:
            raise ErroPedidoClienteNaoEncontrado()
        return cliente

    async def _validate_produto(
        self,
        tenant_id: int,
        produto_id: int,
    ) -> Produto:
        produto = await self.produto_repo.get_by_id(produto_id, tenant_id)
        if produto is None:
            raise ErroPedidoProdutoNaoEncontrado()
        return produto

    async def _recalculate_total(self, order: Order) -> None:
        items = await self.item_repo.list_by_order(order.tenant_id, order.id)
        order.total_amount = sum(item.total_price for item in items)

    async def create(
        self,
        tenant_id: int,
        data: OrderCreate,
        user_id: int | None = None,
    ) -> Order:
        await self._validate_cliente(tenant_id, data.cliente_id)

        produto_ids = [item.produto_id for item in data.items]
        if len(produto_ids) != len(set(produto_ids)):
            raise DuplicateOrderItemError()

        order_number = await self.order_repo.next_order_number(tenant_id)

        order = Order(
            tenant_id=tenant_id,
            order_number=order_number,
            cliente_id=data.cliente_id,
            notes=data.notes,
        )
        await self.order_repo.create(order)

        for item_data in data.items:
            produto = await self._validate_produto(tenant_id, item_data.produto_id)

            unit_price = (
                item_data.unit_price
                if item_data.unit_price is not None
                else produto.price
            )
            total_price = unit_price * item_data.quantity

            item = OrderItem(
                tenant_id=tenant_id,
                order_id=order.id,
                produto_id=produto.id,
                quantity=item_data.quantity,
                unit_price=unit_price,
                total_price=total_price,
            )
            await self.item_repo.create(item)

        await self._recalculate_total(order)
        await self.order_repo.update(order)

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ORDER_CREATE",
            entity_type="order",
            entity_id=order.id,
            new_values={
                "order_number": order.order_number,
                "cliente_id": order.cliente_id,
                "status": order.status,
            },
        )

        return order

    async def update(
        self,
        tenant_id: int,
        order_id: int,
        data: OrderUpdate,
        user_id: int | None = None,
    ) -> Order:
        order = await self.order_repo.get_for_update(tenant_id, order_id)
        if order is None:
            raise OrderNotFoundError()

        if order.status != "DRAFT":
            raise InvalidOrderStateError()

        old_values = {
            "cliente_id": order.cliente_id,
            "notes": order.notes,
        }

        update_data = data.model_dump(exclude_unset=True)

        if "cliente_id" in update_data and update_data["cliente_id"] is not None:
            await self._validate_cliente(tenant_id, update_data["cliente_id"])
            order.cliente_id = update_data["cliente_id"]

        if "notes" in update_data:
            order.notes = update_data["notes"]

        result = await self.order_repo.update(order)

        new_values = {
            "cliente_id": result.cliente_id,
            "notes": result.notes,
        }

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ORDER_UPDATE",
            entity_type="order",
            entity_id=order_id,
            old_values=old_values,
            new_values=new_values,
        )

        return result

    async def add_item(
        self,
        tenant_id: int,
        order_id: int,
        data: OrderItemCreate,
        user_id: int | None = None,
    ) -> OrderItem:
        order = await self.order_repo.get_for_update(tenant_id, order_id)
        if order is None:
            raise OrderNotFoundError()

        if order.status != "DRAFT":
            raise InvalidOrderStateError()

        if await self.item_repo.exists_produto_in_order(
            tenant_id, order_id, data.produto_id
        ):
            raise DuplicateOrderItemError()

        produto = await self._validate_produto(tenant_id, data.produto_id)

        unit_price = data.unit_price if data.unit_price is not None else produto.price
        total_price = unit_price * data.quantity

        item = OrderItem(
            tenant_id=tenant_id,
            order_id=order_id,
            produto_id=produto.id,
            quantity=data.quantity,
            unit_price=unit_price,
            total_price=total_price,
        )
        await self.item_repo.create(item)

        await self._recalculate_total(order)
        await self.order_repo.update(order)

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ORDER_ITEM_ADD",
            entity_type="order_item",
            entity_id=item.id,
            new_values={
                "order_id": order_id,
                "produto_id": produto.id,
                "quantity": str(data.quantity),
                "unit_price": str(unit_price),
            },
        )

        return item

    async def update_item(
        self,
        tenant_id: int,
        order_id: int,
        item_id: int,
        data: OrderItemUpdate,
        user_id: int | None = None,
    ) -> OrderItem:
        order = await self.order_repo.get_for_update(tenant_id, order_id)
        if order is None:
            raise OrderNotFoundError()

        if order.status != "DRAFT":
            raise InvalidOrderStateError()

        item = await self.item_repo.get_by_id_and_order(tenant_id, item_id, order_id)
        if item is None:
            raise OrderItemNotFoundError()

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

        await self._recalculate_total(order)
        await self.order_repo.update(order)

        new_values = {
            "quantity": str(item.quantity),
            "unit_price": str(item.unit_price),
        }

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ORDER_ITEM_UPDATE",
            entity_type="order_item",
            entity_id=item_id,
            old_values=old_values,
            new_values=new_values,
        )

        return item

    async def remove_item(
        self,
        tenant_id: int,
        order_id: int,
        item_id: int,
        user_id: int | None = None,
    ) -> None:
        order = await self.order_repo.get_for_update(tenant_id, order_id)
        if order is None:
            raise OrderNotFoundError()

        if order.status != "DRAFT":
            raise InvalidOrderStateError()

        item = await self.item_repo.get_by_id_and_order(tenant_id, item_id, order_id)
        if item is None:
            raise OrderItemNotFoundError()

        count = await self.item_repo.count_by_order(tenant_id, order_id)
        if count <= 1:
            raise OrderItemRemovalNotAllowedError()

        old_values = {
            "produto_id": item.produto_id,
            "quantity": str(item.quantity),
            "unit_price": str(item.unit_price),
        }

        await self.item_repo.delete(item)

        await self._recalculate_total(order)
        await self.order_repo.update(order)

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ORDER_ITEM_REMOVE",
            entity_type="order_item",
            entity_id=item_id,
            old_values=old_values,
        )

    async def confirm(
        self,
        tenant_id: int,
        order_id: int,
        user_id: int | None = None,
    ) -> Order:
        order = await self.order_repo.get_for_update(tenant_id, order_id)
        if order is None:
            raise OrderNotFoundError()

        if order.status != "DRAFT":
            raise InvalidOrderStateError()

        items = await self.item_repo.list_by_order(tenant_id, order_id)
        if not items:
            raise OrderMustHaveItemsError()

        for item in items:
            produto = await self.produto_repo.get_by_id(item.produto_id, tenant_id)
            if (
                produto is None
                or not produto.is_active
                or produto.deleted_at is not None
            ):
                raise ErroPedidoProdutoInativo()

            inventory = await self.inventory_repo.get_for_update(
                tenant_id, item.produto_id
            )
            if inventory is None:
                raise ErroPedidoProdutoInativo()

            available = inventory.quantity - inventory.reserved_quantity
            if available < item.quantity:
                raise ErroPedidoProdutoInativo()

            inventory.reserved_quantity = inventory.reserved_quantity + item.quantity

            reservation = InventoryReservation(
                tenant_id=tenant_id,
                produto_id=item.produto_id,
                quantity=item.quantity,
                status=ReservationStatus.ACTIVE,
                reference=f"order:{order.id}",
                order_item_id=item.id,
                idempotency_key=f"order:{order.id}:item:{item.id}",
            )
            await self.reservation_repo.create(reservation)

        old_status = order.status
        order.status = "CONFIRMED"
        order.updated_at = datetime.now(UTC)

        result = await self.order_repo.update(order)

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ORDER_CONFIRM",
            entity_type="order",
            entity_id=order_id,
            old_values={"status": old_status},
            new_values={"status": "CONFIRMED"},
        )

        return result

    async def cancel(
        self,
        tenant_id: int,
        order_id: int,
        user_id: int | None = None,
    ) -> Order:
        order = await self.order_repo.get_for_update(tenant_id, order_id)
        if order is None:
            raise OrderNotFoundError()

        if order.status not in VALID_TRANSITIONS:
            raise InvalidOrderStateError()

        reference = f"order:{order.id}"
        reservations = await self.reservation_repo.list_active_by_reference(
            tenant_id, reference
        )
        for reservation in reservations:
            inventory = await self.inventory_repo.get_for_update(
                tenant_id, reservation.produto_id
            )
            if inventory is not None:
                inventory.reserved_quantity = (
                    inventory.reserved_quantity - reservation.quantity
                )

            reservation.status = ReservationStatus.CANCELLED
            reservation.released_at = datetime.now(UTC)
            await self.reservation_repo.update(reservation)

        old_status = order.status
        order.status = "CANCELLED"
        order.updated_at = datetime.now(UTC)

        result = await self.order_repo.update(order)

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ORDER_CANCEL",
            entity_type="order",
            entity_id=order_id,
            old_values={"status": old_status},
            new_values={"status": "CANCELLED"},
        )

        return result

    async def complete(
        self,
        tenant_id: int,
        order_id: int,
        user_id: int | None = None,
    ) -> Order:
        order = await self.order_repo.get_for_update(tenant_id, order_id)
        if order is None:
            raise OrderNotFoundError()

        if order.status != "CONFIRMED":
            raise InvalidOrderStateError()

        reference = f"order:{order.id}"
        reservations = await self.reservation_repo.list_active_by_reference(
            tenant_id, reference
        )
        for reservation in reservations:
            inventory = await self.inventory_repo.get_for_update(
                tenant_id, reservation.produto_id
            )
            if inventory is not None:
                inventory.quantity = inventory.quantity - reservation.quantity
                inventory.reserved_quantity = (
                    inventory.reserved_quantity - reservation.quantity
                )

            reservation.status = ReservationStatus.CONFIRMED
            reservation.confirmed_at = datetime.now(UTC)
            await self.reservation_repo.update(reservation)

        old_status = order.status
        order.status = "COMPLETED"
        order.updated_at = datetime.now(UTC)

        result = await self.order_repo.update(order)

        await self.audit_service.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ORDER_COMPLETE",
            entity_type="order",
            entity_id=order_id,
            old_values={"status": old_status},
            new_values={"status": "COMPLETED"},
        )

        return result
