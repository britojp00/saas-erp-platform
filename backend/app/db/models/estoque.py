from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKeyConstraint, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import (
    BigIntPrimaryKeyMixin,
    EscopoEmpresaMixin,
    SoftDeleteMixin,
    TimestampMixin,
)


class Estoque(
    BigIntPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    EscopoEmpresaMixin,
    Base,
):
    __tablename__ = "estoque"

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "produto_id",
            name="uq_estoque_empresa_produto",
        ),
        ForeignKeyConstraint(
            ["empresa_id", "produto_id"],
            ["produtos.empresa_id", "produtos.id"],
            ondelete="RESTRICT",
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
        default=0,
        server_default="0",
    )

    reserved_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=0,
        server_default="0",
    )
