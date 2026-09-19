from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKeyConstraint, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import (
    BigIntPrimaryKeyMixin,
    SoftDeleteMixin,
    TenantScopedMixin,
    TimestampMixin,
)


class Inventory(
    BigIntPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    TenantScopedMixin,
    Base,
):
    __tablename__ = "inventory"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "product_id",
            name="uq_inventory_tenant_product",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "product_id"],
            ["products.tenant_id", "products.id"],
            ondelete="RESTRICT",
        ),
    )

    product_id: Mapped[int] = mapped_column(
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
