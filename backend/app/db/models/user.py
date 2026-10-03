from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import (
    BigIntPrimaryKeyMixin,
    EscopoEmpresaMixin,
    SoftDeleteMixin,
    TimestampMixin,
)


class User(
    BigIntPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    EscopoEmpresaMixin,
    Base,
):
    __tablename__ = "users"

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "email",
            name="uq_users_empresa_email",
        ),
        UniqueConstraint(
            "empresa_id",
            "id",
            name="uq_users_empresa_id",
        ),
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )
