from sqlalchemy import BigInteger, ForeignKeyConstraint, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import (
    BigIntPrimaryKeyMixin,
    SoftDeleteMixin,
    TenantScopedMixin,
    TimestampMixin,
)


class Categoria(
    BigIntPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    TenantScopedMixin,
    Base,
):
    __tablename__ = "categorias"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "name",
            name="uq_categorias_tenant_name",
        ),
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_categorias_tenant_id",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "parent_id"],
            ["categorias.tenant_id", "categorias.id"],
            ondelete="RESTRICT",
        ),
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    parent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )
