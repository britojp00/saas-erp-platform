from sqlalchemy import Boolean, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import (
    BigIntPrimaryKeyMixin,
    SoftDeleteMixin,
    TimestampMixin,
)


class Tenant(
    BigIntPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    Base,
):
    __tablename__ = "tenants"

    __table_args__ = (
        UniqueConstraint("slug", name="tenants_slug_key"),
        Index("ix_tenants_slug", "slug", unique=True),
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )
