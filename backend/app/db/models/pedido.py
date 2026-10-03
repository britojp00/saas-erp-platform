import enum
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    ForeignKeyConstraint,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import (
    BigIntPrimaryKeyMixin,
    EscopoEmpresaMixin,
    SoftDeleteMixin,
    TimestampMixin,
)


class StatusPedido(str, enum.Enum):
    RASCUNHO = "RASCUNHO"
    CONFIRMADO = "CONFIRMADO"
    CONCLUIDO = "CONCLUIDO"
    CANCELADO = "CANCELADO"


class Pedido(
    BigIntPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    EscopoEmpresaMixin,
    Base,
):
    __tablename__ = "pedidos"

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "numero_pedido",
            name="uq_pedidos_empresa_numero",
        ),
        UniqueConstraint(
            "empresa_id",
            "id",
            name="uq_pedidos_empresa_id",
        ),
        ForeignKeyConstraint(
            ["empresa_id", "cliente_id"],
            ["clientes.empresa_id", "clientes.id"],
            name="fk_pedidos_empresa_cliente",
            ondelete="RESTRICT",
        ),
    )

    numero_pedido: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    cliente_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    status: Mapped[StatusPedido] = mapped_column(
        String(30),
        nullable=False,
        default=StatusPedido.RASCUNHO,
        server_default="RASCUNHO",
        index=True,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=0,
        server_default="0",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
