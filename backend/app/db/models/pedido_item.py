from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKeyConstraint, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import (
    BigIntPrimaryKeyMixin,
    EscopoEmpresaMixin,
    TimestampMixin,
)


class PedidoItem(
    BigIntPrimaryKeyMixin,
    TimestampMixin,
    EscopoEmpresaMixin,
    Base,
):
    __tablename__ = "pedido_itens"

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "pedido_id",
            "produto_id",
            name="uq_pedido_itens_empresa_pedido_produto",
        ),
        ForeignKeyConstraint(
            ["empresa_id", "pedido_id"],
            ["pedidos.empresa_id", "pedidos.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["empresa_id", "produto_id"],
            ["produtos.empresa_id", "produtos.id"],
            ondelete="RESTRICT",
        ),
    )

    pedido_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
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

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    total_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
