from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import (
    BigIntPrimaryKeyMixin,
    EscopoEmpresaMixin,
    SoftDeleteMixin,
    TimestampMixin,
)


class Cliente(
    BigIntPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    EscopoEmpresaMixin,
    Base,
):
    __tablename__ = "clientes"

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "document",
            name="uq_clientes_empresa_document",
        ),
        UniqueConstraint(
            "empresa_id",
            "id",
            name="uq_clientes_empresa_id",
        ),
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    document: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
