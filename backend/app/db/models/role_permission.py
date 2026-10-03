from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKeyConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import EscopoEmpresaMixin


class RolePermission(EscopoEmpresaMixin, Base):
    __tablename__ = "role_permissions"

    __table_args__ = (
        ForeignKeyConstraint(
            ["empresa_id", "role_id"],
            ["roles.empresa_id", "roles.id"],
            name="fk_role_permissions_empresa_role",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["empresa_id", "permission_id"],
            ["permissions.empresa_id", "permissions.id"],
            name="fk_role_permissions_empresa_permission",
            ondelete="CASCADE",
        ),
    )

    role_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    permission_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
