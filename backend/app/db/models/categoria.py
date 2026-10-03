from sqlalchemy import (
    BigInteger,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import (
    BigIntPrimaryKeyMixin,
    EscopoEmpresaMixin,
    SoftDeleteMixin,
    TimestampMixin,
)


class Categoria(
    BigIntPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    EscopoEmpresaMixin,
    Base,
):
    __tablename__ = "categorias"

    __table_args__ = (
        Index(
            "uq_categorias_empresa_name_ativo",
            "empresa_id",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        UniqueConstraint(
            "empresa_id",
            "id",
            name="uq_categorias_empresa_id",
        ),
        ForeignKeyConstraint(
            ["empresa_id", "parent_id"],
            ["categorias.empresa_id", "categorias.id"],
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
