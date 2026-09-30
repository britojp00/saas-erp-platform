from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
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
    SoftDeleteMixin,
    TenantScopedMixin,
    TimestampMixin,
)


class Produto(
    BigIntPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    TenantScopedMixin,
    Base,
):
    __tablename__ = "produtos"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "sku",
            name="uq_produtos_tenant_sku",
        ),
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_produtos_tenant_id",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "categoria_id"],
            ["categorias.tenant_id", "categorias.id"],
            name="fk_produtos_tenant_categoria",
            ondelete="RESTRICT",
        ),
    )

    sku: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    categoria_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    cost_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )
