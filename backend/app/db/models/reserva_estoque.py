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


class StatusReserva(str, enum.Enum):
    ATIVA = "ATIVA"
    CONFIRMADA = "CONFIRMADA"
    LIBERADA = "LIBERADA"
    CANCELADA = "CANCELADA"


class ReservaEstoque(
    BigIntPrimaryKeyMixin,
    TimestampMixin,
    TenantScopedMixin,
    Base,
):
    __tablename__ = "estoque_reservas"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_estoque_reservas_tenant_idempotency",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "produto_id"],
            ["produtos.tenant_id", "produtos.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["order_item_id"],
            ["order_items.id"],
            ondelete="SET NULL",
        ),
    )

    produto_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )

    status: Mapped[StatusReserva] = mapped_column(
        String(20),
        nullable=False,
        default=StatusReserva.ATIVA,
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

    order_item_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )

    reserved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
