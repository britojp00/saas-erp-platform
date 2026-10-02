import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKeyConstraint,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import (
    BigIntPrimaryKeyMixin,
    TenantScopedMixin,
    TimestampMixin,
)


class TipoMovimentacao(str, enum.Enum):
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"
    AJUSTE = "AJUSTE"


class MovimentacaoEstoque(
    BigIntPrimaryKeyMixin,
    TimestampMixin,
    TenantScopedMixin,
    Base,
):
    __tablename__ = "estoque_movimentacoes"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_estoque_movimentacoes_tenant_idempotency",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "produto_id"],
            ["produtos.tenant_id", "produtos.id"],
            ondelete="RESTRICT",
        ),
    )

    produto_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    tipo_movimentacao: Mapped[TipoMovimentacao] = mapped_column(
        String(20),
        nullable=False,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )

    reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
