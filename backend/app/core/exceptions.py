import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.errors")


class AppError(Exception):
    """Base exception for all application errors."""


class AuthenticationError(AppError):
    """Raised when authentication fails."""


class AuthorizationError(AppError):
    """Raised when the user lacks permission."""


class DomainError(AppError):
    """Base exception for business rule violations."""


class UserNotFoundError(DomainError):
    """Raised when a user is not found."""


class InactiveUserError(DomainError):
    """Raised when a user account is inactive."""


class DeletedUserError(DomainError):
    """Raised when a soft-deleted user attempts to authenticate."""


class TenantNotFoundError(DomainError):
    """Raised when a tenant is not found."""


class InactiveTenantError(DomainError):
    """Raised when a tenant is inactive."""


class CustomerNotFoundError(DomainError):
    """Raised when a customer is not found."""


class DuplicateCustomerError(DomainError):
    """Raised when a customer document already exists in the tenant."""


class CategoryNotFoundError(DomainError):
    """Raised when a category is not found."""


class DuplicateCategoryError(DomainError):
    """Raised when a category name already exists in the tenant."""


class CategoryHasChildrenError(DomainError):
    """Raised when trying to delete a category that has children."""


class CategoryHasProductsError(DomainError):
    """Raised when trying to delete a category that is used by products."""


class CategoryCycleError(DomainError):
    """Raised when setting a parent_id would create a cycle."""


class CategorySelfReferenceError(DomainError):
    """Raised when trying to set a category as its own parent."""


class CategoryParentNotFoundError(DomainError):
    """Raised when the specified parent category does not exist."""


class ProductNotFoundError(DomainError):
    """Raised when a product is not found."""


class DuplicateProductError(DomainError):
    """Raised when a product SKU already exists in the tenant."""


class ProductInUseError(DomainError):
    """Raised when trying to delete a product that has inventory or order references."""


class InvalidProductCategoryError(DomainError):
    """Raised when the specified category is invalid for the product."""


class InventoryNotFoundError(DomainError):
    """Raised when an inventory record is not found."""


class InsufficientStockError(DomainError):
    """Raised when there is not enough stock for an operation."""


class InvalidInventoryOperationError(DomainError):
    """Raised when an inventory operation is invalid."""


class ReservationNotFoundError(DomainError):
    """Raised when a reservation is not found."""


class InvalidReservationStateError(DomainError):
    """Raised when a reservation state transition is invalid."""


class DuplicateIdempotencyKeyError(DomainError):
    """Raised when an idempotency key already exists for a different request."""


class OrderNotFoundError(DomainError):
    """Raised when an order is not found."""


class InvalidOrderStateError(DomainError):
    """Raised when an order state transition is invalid."""


class OrderMustHaveItemsError(DomainError):
    """Raised when trying to persist an order without items."""


class DuplicateOrderItemError(DomainError):
    """Raised when a product already exists in the same order."""


class OrderItemNotFoundError(DomainError):
    """Raised when an order item is not found."""


class OrderItemRemovalNotAllowedError(DomainError):
    """Raised when trying to remove the last item from an order."""


class OrderCustomerNotFoundError(DomainError):
    """Raised when the customer for an order is not found."""


class OrderProductNotFoundError(DomainError):
    """Raised when a product for an order item is not found."""


class OrderProductInactiveError(DomainError):
    """Raised when trying to confirm an order with inactive products."""


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        logger.warning(
            "auth.authentication.failed",
            extra={"event": "auth.authentication.failed"},
        )
        return JSONResponse(
            status_code=401,
            content={"detail": "Credenciais inválidas"},
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        logger.warning(
            "auth.authorization.denied",
            extra={"event": "auth.authorization.denied"},
        )
        return JSONResponse(
            status_code=403,
            content={"detail": "Acesso negado"},
        )

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_error_handler(
        request: Request, exc: UserNotFoundError
    ) -> JSONResponse:
        logger.warning(
            "user.not_found",
            extra={"event": "user.not_found"},
        )
        return JSONResponse(
            status_code=404,
            content={"detail": "Usuário não encontrado"},
        )

    @app.exception_handler(TenantNotFoundError)
    async def tenant_not_found_error_handler(
        request: Request, exc: TenantNotFoundError
    ) -> JSONResponse:
        logger.warning(
            "tenant.not_found",
            extra={"event": "tenant.not_found"},
        )
        return JSONResponse(
            status_code=404,
            content={"detail": "Tenant não encontrado"},
        )

    @app.exception_handler(CustomerNotFoundError)
    async def customer_not_found_error_handler(
        request: Request, exc: CustomerNotFoundError
    ) -> JSONResponse:
        logger.warning(
            "customer.not_found",
            extra={"event": "customer.not_found"},
        )
        return JSONResponse(
            status_code=404,
            content={"detail": "Cliente não encontrado"},
        )

    @app.exception_handler(DuplicateCustomerError)
    async def duplicate_customer_error_handler(
        request: Request, exc: DuplicateCustomerError
    ) -> JSONResponse:
        logger.warning(
            "customer.duplicate",
            extra={"event": "customer.duplicate"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "Já existe um cliente com este documento"},
        )

    @app.exception_handler(CategoryNotFoundError)
    async def category_not_found_error_handler(
        request: Request, exc: CategoryNotFoundError
    ) -> JSONResponse:
        logger.warning(
            "category.not_found",
            extra={"event": "category.not_found"},
        )
        return JSONResponse(
            status_code=404,
            content={"detail": "Categoria não encontrada"},
        )

    @app.exception_handler(DuplicateCategoryError)
    async def duplicate_category_error_handler(
        request: Request, exc: DuplicateCategoryError
    ) -> JSONResponse:
        logger.warning(
            "category.duplicate",
            extra={"event": "category.duplicate"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "Já existe uma categoria com este nome"},
        )

    @app.exception_handler(CategoryHasChildrenError)
    async def category_has_children_error_handler(
        request: Request, exc: CategoryHasChildrenError
    ) -> JSONResponse:
        logger.warning(
            "category.has_children",
            extra={"event": "category.has_children"},
        )
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Não é possível excluir uma categoria que possui subcategorias"
            },
        )

    @app.exception_handler(CategoryHasProductsError)
    async def category_has_products_error_handler(
        request: Request, exc: CategoryHasProductsError
    ) -> JSONResponse:
        logger.warning(
            "category.has_products",
            extra={"event": "category.has_products"},
        )
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Não é possível excluir uma categoria que possui produtos vinculados"
            },
        )

    @app.exception_handler(CategoryCycleError)
    async def category_cycle_error_handler(
        request: Request, exc: CategoryCycleError
    ) -> JSONResponse:
        logger.warning(
            "category.cycle_detected",
            extra={"event": "category.cycle_detected"},
        )
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Definir esta categoria como pai criaria um ciclo na hierarquia"
            },
        )

    @app.exception_handler(CategorySelfReferenceError)
    async def category_self_reference_error_handler(
        request: Request, exc: CategorySelfReferenceError
    ) -> JSONResponse:
        logger.warning(
            "category.self_reference",
            extra={"event": "category.self_reference"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "Uma categoria não pode ser pai de si mesma"},
        )

    @app.exception_handler(CategoryParentNotFoundError)
    async def category_parent_not_found_error_handler(
        request: Request, exc: CategoryParentNotFoundError
    ) -> JSONResponse:
        logger.warning(
            "category.parent_not_found",
            extra={"event": "category.parent_not_found"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "A categoria pai especificada não existe"},
        )

    @app.exception_handler(ProductNotFoundError)
    async def product_not_found_error_handler(
        request: Request, exc: ProductNotFoundError
    ) -> JSONResponse:
        logger.warning(
            "product.not_found",
            extra={"event": "product.not_found"},
        )
        return JSONResponse(
            status_code=404,
            content={"detail": "Produto não encontrado"},
        )

    @app.exception_handler(DuplicateProductError)
    async def duplicate_product_error_handler(
        request: Request, exc: DuplicateProductError
    ) -> JSONResponse:
        logger.warning(
            "product.duplicate",
            extra={"event": "product.duplicate"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "Já existe um produto com este SKU"},
        )

    @app.exception_handler(ProductInUseError)
    async def product_in_use_error_handler(
        request: Request, exc: ProductInUseError
    ) -> JSONResponse:
        logger.warning(
            "product.in_use",
            extra={"event": "product.in_use"},
        )
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Não é possível excluir um produto que possui estoque ou pedidos vinculados"
            },
        )

    @app.exception_handler(InvalidProductCategoryError)
    async def invalid_product_category_error_handler(
        request: Request, exc: InvalidProductCategoryError
    ) -> JSONResponse:
        logger.warning(
            "product.invalid_category",
            extra={"event": "product.invalid_category"},
        )
        return JSONResponse(
            status_code=409,
            content={
                "detail": "A categoria especificada não é válida para este produto"
            },
        )

    @app.exception_handler(InventoryNotFoundError)
    async def inventory_not_found_error_handler(
        request: Request, exc: InventoryNotFoundError
    ) -> JSONResponse:
        logger.warning(
            "inventory.not_found",
            extra={"event": "inventory.not_found"},
        )
        return JSONResponse(
            status_code=404,
            content={"detail": "Registro de estoque não encontrado"},
        )

    @app.exception_handler(InsufficientStockError)
    async def insufficient_stock_error_handler(
        request: Request, exc: InsufficientStockError
    ) -> JSONResponse:
        logger.warning(
            "inventory.insufficient_stock",
            extra={"event": "inventory.insufficient_stock"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "Estoque insuficiente para esta operação"},
        )

    @app.exception_handler(InvalidInventoryOperationError)
    async def invalid_inventory_operation_error_handler(
        request: Request, exc: InvalidInventoryOperationError
    ) -> JSONResponse:
        logger.warning(
            "inventory.invalid_operation",
            extra={"event": "inventory.invalid_operation"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "Operação de estoque inválida"},
        )

    @app.exception_handler(ReservationNotFoundError)
    async def reservation_not_found_error_handler(
        request: Request, exc: ReservationNotFoundError
    ) -> JSONResponse:
        logger.warning(
            "reservation.not_found",
            extra={"event": "reservation.not_found"},
        )
        return JSONResponse(
            status_code=404,
            content={"detail": "Reserva não encontrada"},
        )

    @app.exception_handler(InvalidReservationStateError)
    async def invalid_reservation_state_error_handler(
        request: Request, exc: InvalidReservationStateError
    ) -> JSONResponse:
        logger.warning(
            "reservation.invalid_state",
            extra={"event": "reservation.invalid_state"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "Transição de estado da reserva é inválida"},
        )

    @app.exception_handler(DuplicateIdempotencyKeyError)
    async def duplicate_idempotency_key_error_handler(
        request: Request, exc: DuplicateIdempotencyKeyError
    ) -> JSONResponse:
        logger.warning(
            "idempotency.duplicate_key",
            extra={"event": "idempotency.duplicate_key"},
        )
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Chave de idempotência já utilizada para uma operação diferente"
            },
        )

    @app.exception_handler(OrderNotFoundError)
    async def order_not_found_error_handler(
        request: Request, exc: OrderNotFoundError
    ) -> JSONResponse:
        logger.warning(
            "order.not_found",
            extra={"event": "order.not_found"},
        )
        return JSONResponse(
            status_code=404,
            content={"detail": "Pedido não encontrado"},
        )

    @app.exception_handler(InvalidOrderStateError)
    async def invalid_order_state_error_handler(
        request: Request, exc: InvalidOrderStateError
    ) -> JSONResponse:
        logger.warning(
            "order.invalid_state",
            extra={"event": "order.invalid_state"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "Transição de estado do pedido é inválida"},
        )

    @app.exception_handler(OrderMustHaveItemsError)
    async def order_must_have_items_error_handler(
        request: Request, exc: OrderMustHaveItemsError
    ) -> JSONResponse:
        logger.warning(
            "order.must_have_items",
            extra={"event": "order.must_have_items"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "O pedido deve possuir pelo menos um item"},
        )

    @app.exception_handler(DuplicateOrderItemError)
    async def duplicate_order_item_error_handler(
        request: Request, exc: DuplicateOrderItemError
    ) -> JSONResponse:
        logger.warning(
            "order.duplicate_item",
            extra={"event": "order.duplicate_item"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "Já existe um item com este produto no pedido"},
        )

    @app.exception_handler(OrderItemNotFoundError)
    async def order_item_not_found_error_handler(
        request: Request, exc: OrderItemNotFoundError
    ) -> JSONResponse:
        logger.warning(
            "order_item.not_found",
            extra={"event": "order_item.not_found"},
        )
        return JSONResponse(
            status_code=404,
            content={"detail": "Item do pedido não encontrado"},
        )

    @app.exception_handler(OrderItemRemovalNotAllowedError)
    async def order_item_removal_not_allowed_error_handler(
        request: Request, exc: OrderItemRemovalNotAllowedError
    ) -> JSONResponse:
        logger.warning(
            "order_item.removal_not_allowed",
            extra={"event": "order_item.removal_not_allowed"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "Não é possível remover o último item do pedido"},
        )

    @app.exception_handler(OrderCustomerNotFoundError)
    async def order_customer_not_found_error_handler(
        request: Request, exc: OrderCustomerNotFoundError
    ) -> JSONResponse:
        logger.warning(
            "order.customer_not_found",
            extra={"event": "order.customer_not_found"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "Cliente do pedido não encontrado"},
        )

    @app.exception_handler(OrderProductNotFoundError)
    async def order_product_not_found_error_handler(
        request: Request, exc: OrderProductNotFoundError
    ) -> JSONResponse:
        logger.warning(
            "order.product_not_found",
            extra={"event": "order.product_not_found"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "Produto do item não encontrado"},
        )

    @app.exception_handler(OrderProductInactiveError)
    async def order_product_inactive_error_handler(
        request: Request, exc: OrderProductInactiveError
    ) -> JSONResponse:
        logger.warning(
            "order.product_inactive",
            extra={"event": "order.product_inactive"},
        )
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Todos os produtos devem estar ativos para confirmar o pedido"
            },
        )
