from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DuplicateIdempotencyKeyError,
    InsufficientStockError,
    InvalidInventoryOperationError,
    InvalidReservationStateError,
    InventoryNotFoundError,
    ProductNotFoundError,
    ReservationNotFoundError,
)
from app.db.models.inventory import Inventory
from app.db.models.inventory_movement import InventoryMovement, MovementType
from app.db.models.inventory_reservation import InventoryReservation, ReservationStatus
from app.db.models.product import Product
from app.repositories.inventory import InventoryRepository
from app.repositories.inventory_movement import InventoryMovementRepository
from app.repositories.inventory_reservation import InventoryReservationRepository
from app.repositories.product import ProductRepository
from app.schemas.inventory import MovementCreate, ReservationCreate


class InventoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.inventory_repo = InventoryRepository(session)
        self.movement_repo = InventoryMovementRepository(session)
        self.reservation_repo = InventoryReservationRepository(session)
        self.product_repo = ProductRepository(session)

    async def _validate_product_exists(
        self,
        tenant_id: int,
        product_id: int,
    ) -> Product:
        product = await self.product_repo.get_by_id(product_id, tenant_id)
        if product is None:
            raise ProductNotFoundError()
        return product

    async def list_balances(
        self,
        tenant_id: int,
        *,
        page: int,
        page_size: int,
        product_id: int | None = None,
    ) -> tuple[list[Inventory], int]:
        offset = (page - 1) * page_size
        return await self.inventory_repo.list(
            tenant_id,
            offset=offset,
            limit=page_size,
            product_id=product_id,
        )

    async def get_balance(
        self,
        tenant_id: int,
        product_id: int,
    ) -> Inventory:
        inventory = await self.inventory_repo.get_by_product_id(tenant_id, product_id)
        if inventory is None:
            raise InventoryNotFoundError()
        return inventory

    async def list_movements(
        self,
        tenant_id: int,
        *,
        page: int,
        page_size: int,
        product_id: int | None = None,
    ) -> tuple[list[InventoryMovement], int]:
        offset = (page - 1) * page_size
        return await self.movement_repo.list(
            tenant_id,
            offset=offset,
            limit=page_size,
            product_id=product_id,
        )

    async def list_reservations(
        self,
        tenant_id: int,
        *,
        page: int,
        page_size: int,
        product_id: int | None = None,
    ) -> tuple[list[InventoryReservation], int]:
        offset = (page - 1) * page_size
        return await self.reservation_repo.list(
            tenant_id,
            offset=offset,
            limit=page_size,
            product_id=product_id,
        )

    async def create_movement(
        self,
        tenant_id: int,
        data: MovementCreate,
    ) -> InventoryMovement:
        await self._validate_product_exists(tenant_id, data.product_id)

        if data.movement_type == "ADJUSTMENT" and data.quantity <= 0:
            raise InvalidInventoryOperationError()

        existing = await self.movement_repo.exists_by_idempotency_key(
            tenant_id, data.idempotency_key
        )
        if existing:
            raise DuplicateIdempotencyKeyError()

        inventory = await self.inventory_repo.get_for_update(tenant_id, data.product_id)
        if inventory is None:
            inventory = Inventory(
                tenant_id=tenant_id,
                product_id=data.product_id,
            )
            self.session.add(inventory)
            await self.session.flush()

        if data.movement_type == "IN":
            inventory.quantity = inventory.quantity + data.quantity
        elif data.movement_type == "OUT":
            available = inventory.quantity - inventory.reserved_quantity
            if available < data.quantity:
                raise InsufficientStockError()
            inventory.quantity = inventory.quantity - data.quantity
        elif data.movement_type == "ADJUSTMENT":
            inventory.quantity = data.quantity
            if inventory.reserved_quantity > inventory.quantity:
                raise InvalidInventoryOperationError()

        movement = InventoryMovement(
            tenant_id=tenant_id,
            product_id=data.product_id,
            movement_type=MovementType(data.movement_type),
            quantity=data.quantity,
            reference=data.reference,
            notes=data.notes,
            idempotency_key=data.idempotency_key,
        )

        return await self.movement_repo.create(movement)

    async def create_reservation(
        self,
        tenant_id: int,
        data: ReservationCreate,
    ) -> InventoryReservation:
        product = await self._validate_product_exists(tenant_id, data.product_id)

        if not product.is_active:
            raise InvalidInventoryOperationError()

        existing = await self.reservation_repo.exists_by_idempotency_key(
            tenant_id, data.idempotency_key
        )
        if existing:
            raise DuplicateIdempotencyKeyError()

        inventory = await self.inventory_repo.get_for_update(tenant_id, data.product_id)
        if inventory is None:
            raise InventoryNotFoundError()

        available = inventory.quantity - inventory.reserved_quantity
        if available < data.quantity:
            raise InsufficientStockError()

        inventory.reserved_quantity = inventory.reserved_quantity + data.quantity

        reservation = InventoryReservation(
            tenant_id=tenant_id,
            product_id=data.product_id,
            quantity=data.quantity,
            status=ReservationStatus.ACTIVE,
            reference=data.reference,
            notes=data.notes,
            idempotency_key=data.idempotency_key,
            order_item_id=data.order_item_id,
        )

        return await self.reservation_repo.create(reservation)

    async def confirm_reservation(
        self,
        tenant_id: int,
        reservation_id: int,
    ) -> InventoryReservation:
        reservation = await self.reservation_repo.get_by_id(tenant_id, reservation_id)
        if reservation is None:
            raise ReservationNotFoundError()

        if reservation.status != ReservationStatus.ACTIVE:
            raise InvalidReservationStateError()

        inventory = await self.inventory_repo.get_for_update(
            tenant_id, reservation.product_id
        )
        if inventory is None:
            raise InventoryNotFoundError()

        from datetime import UTC, datetime

        reservation.status = ReservationStatus.CONFIRMED
        reservation.confirmed_at = datetime.now(UTC)
        inventory.reserved_quantity = inventory.reserved_quantity - reservation.quantity

        return await self.reservation_repo.update(reservation)

    async def release_reservation(
        self,
        tenant_id: int,
        reservation_id: int,
    ) -> InventoryReservation:
        reservation = await self.reservation_repo.get_by_id(tenant_id, reservation_id)
        if reservation is None:
            raise ReservationNotFoundError()

        if reservation.status != ReservationStatus.ACTIVE:
            raise InvalidReservationStateError()

        inventory = await self.inventory_repo.get_for_update(
            tenant_id, reservation.product_id
        )
        if inventory is None:
            raise InventoryNotFoundError()

        from datetime import UTC, datetime

        reservation.status = ReservationStatus.RELEASED
        reservation.released_at = datetime.now(UTC)
        inventory.reserved_quantity = inventory.reserved_quantity - reservation.quantity

        return await self.reservation_repo.update(reservation)

    async def cancel_reservation(
        self,
        tenant_id: int,
        reservation_id: int,
    ) -> InventoryReservation:
        reservation = await self.reservation_repo.get_by_id(tenant_id, reservation_id)
        if reservation is None:
            raise ReservationNotFoundError()

        if reservation.status != ReservationStatus.ACTIVE:
            raise InvalidReservationStateError()

        inventory = await self.inventory_repo.get_for_update(
            tenant_id, reservation.product_id
        )
        if inventory is None:
            raise InventoryNotFoundError()

        from datetime import UTC, datetime

        reservation.status = ReservationStatus.CANCELLED
        reservation.released_at = datetime.now(UTC)
        inventory.reserved_quantity = inventory.reserved_quantity - reservation.quantity

        return await self.reservation_repo.update(reservation)
