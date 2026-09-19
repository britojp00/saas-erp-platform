from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKeyConstraint, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import (
    BigIntPrimaryKeyMixin,
    TenantScopedMixin,
    TimestampMixin,
)


class OrderItem(
    BigIntPrimaryKeyMixin,
    TimestampMixin,
    TenantScopedMixin,
    Base,
):
    __tablename__ = "order_items"

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "order_id"],
            ["orders.tenant_id", "orders.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "product_id"],
            ["products.tenant_id", "products.id"],
            ondelete="RESTRICT",
        ),
    )

    order_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
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
