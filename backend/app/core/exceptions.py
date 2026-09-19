from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


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


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"detail": "Credenciais inválidas"},
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"detail": "Acesso negado"},
        )

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_error_handler(
        request: Request, exc: UserNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": "Usuário não encontrado"},
        )

    @app.exception_handler(TenantNotFoundError)
    async def tenant_not_found_error_handler(
        request: Request, exc: TenantNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": "Tenant não encontrado"},
        )

    @app.exception_handler(CustomerNotFoundError)
    async def customer_not_found_error_handler(
        request: Request, exc: CustomerNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": "Cliente não encontrado"},
        )

    @app.exception_handler(DuplicateCustomerError)
    async def duplicate_customer_error_handler(
        request: Request, exc: DuplicateCustomerError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "Já existe um cliente com este documento"},
        )

    @app.exception_handler(CategoryNotFoundError)
    async def category_not_found_error_handler(
        request: Request, exc: CategoryNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": "Categoria não encontrada"},
        )

    @app.exception_handler(DuplicateCategoryError)
    async def duplicate_category_error_handler(
        request: Request, exc: DuplicateCategoryError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "Já existe uma categoria com este nome"},
        )

    @app.exception_handler(CategoryHasChildrenError)
    async def category_has_children_error_handler(
        request: Request, exc: CategoryHasChildrenError
    ) -> JSONResponse:
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
        return JSONResponse(
            status_code=409,
            content={"detail": "Uma categoria não pode ser pai de si mesma"},
        )

    @app.exception_handler(CategoryParentNotFoundError)
    async def category_parent_not_found_error_handler(
        request: Request, exc: CategoryParentNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "A categoria pai especificada não existe"},
        )

    @app.exception_handler(ProductNotFoundError)
    async def product_not_found_error_handler(
        request: Request, exc: ProductNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": "Produto não encontrado"},
        )

    @app.exception_handler(DuplicateProductError)
    async def duplicate_product_error_handler(
        request: Request, exc: DuplicateProductError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "Já existe um produto com este SKU"},
        )

    @app.exception_handler(ProductInUseError)
    async def product_in_use_error_handler(
        request: Request, exc: ProductInUseError
    ) -> JSONResponse:
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
        return JSONResponse(
            status_code=404,
            content={"detail": "Registro de estoque não encontrado"},
        )

    @app.exception_handler(InsufficientStockError)
    async def insufficient_stock_error_handler(
        request: Request, exc: InsufficientStockError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "Estoque insuficiente para esta operação"},
        )

    @app.exception_handler(InvalidInventoryOperationError)
    async def invalid_inventory_operation_error_handler(
        request: Request, exc: InvalidInventoryOperationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "Operação de estoque inválida"},
        )

    @app.exception_handler(ReservationNotFoundError)
    async def reservation_not_found_error_handler(
        request: Request, exc: ReservationNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": "Reserva não encontrada"},
        )

    @app.exception_handler(InvalidReservationStateError)
    async def invalid_reservation_state_error_handler(
        request: Request, exc: InvalidReservationStateError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "Transição de estado da reserva é inválida"},
        )

    @app.exception_handler(DuplicateIdempotencyKeyError)
    async def duplicate_idempotency_key_error_handler(
        request: Request, exc: DuplicateIdempotencyKeyError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Chave de idempotência já utilizada para uma operação diferente"
            },
        )
