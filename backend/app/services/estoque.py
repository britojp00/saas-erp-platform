from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ErroChaveIdempotenciaDuplicada,
    ErroEstadoReservaInvalido,
    ErroEstoqueInsuficiente,
    ErroEstoqueNaoEncontrado,
    ErroOperacaoEstoqueInvalida,
    ErroProdutoNaoEncontrado,
    ErroReservaNaoEncontrada,
)
from app.db.models.estoque import Estoque
from app.db.models.movimentacao_estoque import MovimentacaoEstoque, TipoMovimentacao
from app.db.models.produto import Produto
from app.db.models.reserva_estoque import ReservaEstoque, StatusReserva
from app.repositories.estoque import EstoqueRepository
from app.repositories.movimentacao_estoque import MovimentacaoEstoqueRepository
from app.repositories.produto import ProdutoRepository
from app.repositories.reserva_estoque import ReservaEstoqueRepository
from app.schemas.estoque import MovimentacaoCriarPayload, ReservaCriarPayload
from app.services.audit_log import AuditLogService


class EstoqueService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.estoque_repo = EstoqueRepository(session)
        self.movimentacao_repo = MovimentacaoEstoqueRepository(session)
        self.reserva_repo = ReservaEstoqueRepository(session)
        self.produto_repo = ProdutoRepository(session)
        self.audit_service = AuditLogService(session)

    async def _validate_produto_exists(
        self,
        empresa_id: int,
        produto_id: int,
    ) -> Produto:
        produto = await self.produto_repo.get_by_id(produto_id, empresa_id)
        if produto is None:
            raise ErroProdutoNaoEncontrado()
        return produto

    async def list_saldos(
        self,
        empresa_id: int,
        *,
        page: int,
        page_size: int,
        produto_id: int | None = None,
    ) -> tuple[list[Estoque], int]:
        offset = (page - 1) * page_size
        return await self.estoque_repo.list(
            empresa_id,
            offset=offset,
            limit=page_size,
            produto_id=produto_id,
        )

    async def get_saldo(
        self,
        empresa_id: int,
        produto_id: int,
    ) -> Estoque:
        estoque = await self.estoque_repo.get_by_produto_id(empresa_id, produto_id)
        if estoque is None:
            raise ErroEstoqueNaoEncontrado()
        return estoque

    async def list_movimentacoes(
        self,
        empresa_id: int,
        *,
        page: int,
        page_size: int,
        produto_id: int | None = None,
    ) -> tuple[list[MovimentacaoEstoque], int]:
        offset = (page - 1) * page_size
        return await self.movimentacao_repo.list(
            empresa_id,
            offset=offset,
            limit=page_size,
            produto_id=produto_id,
        )

    async def list_reservas(
        self,
        empresa_id: int,
        *,
        page: int,
        page_size: int,
        produto_id: int | None = None,
    ) -> tuple[list[ReservaEstoque], int]:
        offset = (page - 1) * page_size
        return await self.reserva_repo.list(
            empresa_id,
            offset=offset,
            limit=page_size,
            produto_id=produto_id,
        )

    async def create_movimentacao(
        self,
        empresa_id: int,
        data: MovimentacaoCriarPayload,
        user_id: int | None = None,
    ) -> MovimentacaoEstoque:
        await self._validate_produto_exists(empresa_id, data.produto_id)

        if data.tipo_movimentacao == "AJUSTE" and data.quantity <= 0:
            raise ErroOperacaoEstoqueInvalida()

        existing = await self.movimentacao_repo.exists_by_idempotency_key(
            empresa_id, data.idempotency_key
        )
        if existing:
            raise ErroChaveIdempotenciaDuplicada()

        estoque = await self.estoque_repo.get_for_update(empresa_id, data.produto_id)
        if estoque is None:
            estoque = Estoque(
                empresa_id=empresa_id,
                produto_id=data.produto_id,
            )
            self.session.add(estoque)
            await self.session.flush()

        old_quantity = estoque.quantity

        if data.tipo_movimentacao == "ENTRADA":
            estoque.quantity = estoque.quantity + data.quantity
        elif data.tipo_movimentacao == "SAIDA":
            available = estoque.quantity - estoque.reserved_quantity
            if available < data.quantity:
                raise ErroEstoqueInsuficiente()
            estoque.quantity = estoque.quantity - data.quantity
        elif data.tipo_movimentacao == "AJUSTE":
            estoque.quantity = data.quantity
            if estoque.reserved_quantity > estoque.quantity:
                raise ErroOperacaoEstoqueInvalida()

        movimentacao = MovimentacaoEstoque(
            empresa_id=empresa_id,
            produto_id=data.produto_id,
            tipo_movimentacao=TipoMovimentacao(data.tipo_movimentacao),
            quantity=data.quantity,
            reference=data.reference,
            notes=data.notes,
            idempotency_key=data.idempotency_key,
        )

        result = await self.movimentacao_repo.create(movimentacao)

        action_map = {
            "ENTRADA": "ESTOQUE_ENTRADA",
            "SAIDA": "ESTOQUE_SAIDA",
            "AJUSTE": "ESTOQUE_AJUSTE",
        }

        await self.audit_service.log(
            empresa_id=empresa_id,
            user_id=user_id,
            action=action_map[data.tipo_movimentacao],
            entity_type="estoque",
            entity_id=estoque.produto_id,
            old_values={"quantity": str(old_quantity)},
            new_values={"quantity": str(estoque.quantity)},
        )

        return result

    async def create_reserva(
        self,
        empresa_id: int,
        data: ReservaCriarPayload,
        user_id: int | None = None,
    ) -> ReservaEstoque:
        produto = await self._validate_produto_exists(empresa_id, data.produto_id)

        if not produto.is_active:
            raise ErroOperacaoEstoqueInvalida()

        existing = await self.reserva_repo.exists_by_idempotency_key(
            empresa_id, data.idempotency_key
        )
        if existing:
            raise ErroChaveIdempotenciaDuplicada()

        estoque = await self.estoque_repo.get_for_update(empresa_id, data.produto_id)
        if estoque is None:
            raise ErroEstoqueNaoEncontrado()

        available = estoque.quantity - estoque.reserved_quantity
        if available < data.quantity:
            raise ErroEstoqueInsuficiente()

        estoque.reserved_quantity = estoque.reserved_quantity + data.quantity

        reserva = ReservaEstoque(
            empresa_id=empresa_id,
            produto_id=data.produto_id,
            quantity=data.quantity,
            status=StatusReserva.ATIVA,
            reference=data.reference,
            notes=data.notes,
            idempotency_key=data.idempotency_key,
            pedido_item_id=data.pedido_item_id,
        )

        result = await self.reserva_repo.create(reserva)

        await self.audit_service.log(
            empresa_id=empresa_id,
            user_id=user_id,
            action="RESERVA_CRIAR",
            entity_type="reserva",
            entity_id=result.id,
            new_values={
                "produto_id": data.produto_id,
                "quantity": str(data.quantity),
                "reference": data.reference,
            },
        )

        return result

    async def confirm_reserva(
        self,
        empresa_id: int,
        reserva_id: int,
        user_id: int | None = None,
    ) -> ReservaEstoque:
        reserva = await self.reserva_repo.get_by_id(empresa_id, reserva_id)
        if reserva is None:
            raise ErroReservaNaoEncontrada()

        if reserva.status != StatusReserva.ATIVA:
            raise ErroEstadoReservaInvalido()

        estoque = await self.estoque_repo.get_for_update(empresa_id, reserva.produto_id)
        if estoque is None:
            raise ErroEstoqueNaoEncontrado()

        from datetime import UTC, datetime

        reserva.status = StatusReserva.CONFIRMADA
        reserva.confirmed_at = datetime.now(UTC)
        estoque.reserved_quantity = estoque.reserved_quantity - reserva.quantity

        result = await self.reserva_repo.update(reserva)

        await self.audit_service.log(
            empresa_id=empresa_id,
            user_id=user_id,
            action="RESERVA_CONFIRMAR",
            entity_type="reserva",
            entity_id=reserva_id,
            old_values={"status": "ATIVA"},
            new_values={"status": "CONFIRMADA"},
        )

        return result

    async def release_reserva(
        self,
        empresa_id: int,
        reserva_id: int,
        user_id: int | None = None,
    ) -> ReservaEstoque:
        reserva = await self.reserva_repo.get_by_id(empresa_id, reserva_id)
        if reserva is None:
            raise ErroReservaNaoEncontrada()

        if reserva.status != StatusReserva.ATIVA:
            raise ErroEstadoReservaInvalido()

        estoque = await self.estoque_repo.get_for_update(empresa_id, reserva.produto_id)
        if estoque is None:
            raise ErroEstoqueNaoEncontrado()

        from datetime import UTC, datetime

        reserva.status = StatusReserva.LIBERADA
        reserva.released_at = datetime.now(UTC)
        estoque.reserved_quantity = estoque.reserved_quantity - reserva.quantity

        result = await self.reserva_repo.update(reserva)

        await self.audit_service.log(
            empresa_id=empresa_id,
            user_id=user_id,
            action="RESERVA_LIBERAR",
            entity_type="reserva",
            entity_id=reserva_id,
            old_values={"status": "ATIVA"},
            new_values={"status": "LIBERADA"},
        )

        return result

    async def cancel_reserva(
        self,
        empresa_id: int,
        reserva_id: int,
        user_id: int | None = None,
    ) -> ReservaEstoque:
        reserva = await self.reserva_repo.get_by_id(empresa_id, reserva_id)
        if reserva is None:
            raise ErroReservaNaoEncontrada()

        if reserva.status != StatusReserva.ATIVA:
            raise ErroEstadoReservaInvalido()

        estoque = await self.estoque_repo.get_for_update(empresa_id, reserva.produto_id)
        if estoque is None:
            raise ErroEstoqueNaoEncontrado()

        from datetime import UTC, datetime

        reserva.status = StatusReserva.CANCELADA
        reserva.released_at = datetime.now(UTC)
        estoque.reserved_quantity = estoque.reserved_quantity - reserva.quantity

        result = await self.reserva_repo.update(reserva)

        await self.audit_service.log(
            empresa_id=empresa_id,
            user_id=user_id,
            action="RESERVA_CANCELAR",
            entity_type="reserva",
            entity_id=reserva_id,
            old_values={"status": "ATIVA"},
            new_values={"status": "CANCELADA"},
        )

        return result
