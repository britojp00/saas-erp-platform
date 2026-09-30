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


class ErroClienteNaoEncontrado(DomainError):
    """Levantado quando um cliente não é encontrado."""


class ErroClienteDuplicado(DomainError):
    """Levantado quando o documento de um cliente já existe no tenant."""


class ErroCategoriaNaoEncontrada(DomainError):
    """Levantado quando uma categoria não é encontrada."""


class ErroCategoriaDuplicada(DomainError):
    """Levantado quando o nome de uma categoria já existe no tenant."""


class ErroCategoriaPossuiFilhos(DomainError):
    """Levantado ao tentar excluir uma categoria que possui subcategorias."""


class ErroCategoriaPossuiProdutos(DomainError):
    """Levantado ao tentar excluir uma categoria que é usada por produtos."""


class ErroCategoriaCicloDetectado(DomainError):
    """Levantado quando definir um parent_id criaria um ciclo."""


class ErroCategoriaAutorreferencia(DomainError):
    """Levantado ao tentar definir uma categoria como pai de si mesma."""


class ErroCategoriaPaiNaoEncontrada(DomainError):
    """Levantado quando a categoria pai especificada não existe."""


class ProductNotFoundError(DomainError):
    """Raised when a product is not found."""


class DuplicateProductError(DomainError):
    """Raised when a product SKU already exists in the tenant."""


class ProductInUseError(DomainError):
    """Raised when trying to delete a product that has inventory or order references."""


class ErroProdutoCategoriaInvalida(DomainError):
    """Levantado quando a categoria especificada é inválida para o produto."""


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


class ErroPedidoClienteNaoEncontrado(DomainError):
    """Levantado quando o cliente de um pedido não é encontrado."""


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

    @app.exception_handler(ErroClienteNaoEncontrado)
    async def cliente_nao_encontrado_error_handler(
        request: Request, exc: ErroClienteNaoEncontrado
    ) -> JSONResponse:
        logger.warning(
            "cliente.nao_encontrado",
            extra={"event": "cliente.nao_encontrado"},
        )
        return JSONResponse(
            status_code=404,
            content={"detail": "Cliente não encontrado"},
        )

    @app.exception_handler(ErroClienteDuplicado)
    async def cliente_duplicado_error_handler(
        request: Request, exc: ErroClienteDuplicado
    ) -> JSONResponse:
        logger.warning(
            "cliente.duplicado",
            extra={"event": "cliente.duplicado"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "Já existe um cliente com este documento"},
        )

    @app.exception_handler(ErroCategoriaNaoEncontrada)
    async def categoria_nao_encontrada_error_handler(
        request: Request, exc: ErroCategoriaNaoEncontrada
    ) -> JSONResponse:
        logger.warning(
            "categoria.nao_encontrada",
            extra={"event": "categoria.nao_encontrada"},
        )
        return JSONResponse(
            status_code=404,
            content={"detail": "Categoria não encontrada"},
        )

    @app.exception_handler(ErroCategoriaDuplicada)
    async def categoria_duplicada_error_handler(
        request: Request, exc: ErroCategoriaDuplicada
    ) -> JSONResponse:
        logger.warning(
            "categoria.duplicada",
            extra={"event": "categoria.duplicada"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "Já existe uma categoria com este nome"},
        )

    @app.exception_handler(ErroCategoriaPossuiFilhos)
    async def categoria_possui_filhos_error_handler(
        request: Request, exc: ErroCategoriaPossuiFilhos
    ) -> JSONResponse:
        logger.warning(
            "categoria.possui_filhos",
            extra={"event": "categoria.possui_filhos"},
        )
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Não é possível excluir uma categoria que possui subcategorias"
            },
        )

    @app.exception_handler(ErroCategoriaPossuiProdutos)
    async def categoria_possui_produtos_error_handler(
        request: Request, exc: ErroCategoriaPossuiProdutos
    ) -> JSONResponse:
        logger.warning(
            "categoria.possui_produtos",
            extra={"event": "categoria.possui_produtos"},
        )
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Não é possível excluir uma categoria que possui produtos vinculados"
            },
        )

    @app.exception_handler(ErroCategoriaCicloDetectado)
    async def categoria_ciclo_detectado_error_handler(
        request: Request, exc: ErroCategoriaCicloDetectado
    ) -> JSONResponse:
        logger.warning(
            "categoria.ciclo_detectado",
            extra={"event": "categoria.ciclo_detectado"},
        )
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Definir esta categoria como pai criaria um ciclo na hierarquia"
            },
        )

    @app.exception_handler(ErroCategoriaAutorreferencia)
    async def categoria_autorreferencia_error_handler(
        request: Request, exc: ErroCategoriaAutorreferencia
    ) -> JSONResponse:
        logger.warning(
            "categoria.autorreferencia",
            extra={"event": "categoria.autorreferencia"},
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "Uma categoria não pode ser pai de si mesma"},
        )

    @app.exception_handler(ErroCategoriaPaiNaoEncontrada)
    async def categoria_pai_nao_encontrada_error_handler(
        request: Request, exc: ErroCategoriaPaiNaoEncontrada
    ) -> JSONResponse:
        logger.warning(
            "categoria.pai_nao_encontrada",
            extra={"event": "categoria.pai_nao_encontrada"},
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

    @app.exception_handler(ErroProdutoCategoriaInvalida)
    async def produto_categoria_invalida_error_handler(
        request: Request, exc: ErroProdutoCategoriaInvalida
    ) -> JSONResponse:
        logger.warning(
            "product.categoria_invalida",
            extra={"event": "product.categoria_invalida"},
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

    @app.exception_handler(ErroPedidoClienteNaoEncontrado)
    async def pedido_cliente_nao_encontrado_error_handler(
        request: Request, exc: ErroPedidoClienteNaoEncontrado
    ) -> JSONResponse:
        logger.warning(
            "pedido.cliente_nao_encontrado",
            extra={"event": "pedido.cliente_nao_encontrado"},
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
