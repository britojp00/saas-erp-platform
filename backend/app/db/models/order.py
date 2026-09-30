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
    SoftDeleteMixin,
    TenantScopedMixin,
    TimestampMixin,
)


class Order(
    BigIntPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    TenantScopedMixin,
    Base,
):
    __tablename__ = "orders"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "order_number",
            name="uq_orders_tenant_number",
        ),
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_orders_tenant_id",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "cliente_id"],
            ["clientes.tenant_id", "clientes.id"],
            name="fk_orders_tenant_cliente",
            ondelete="RESTRICT",
        ),
    )

    order_number: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    cliente_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
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
