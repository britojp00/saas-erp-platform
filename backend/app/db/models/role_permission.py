from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKeyConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TenantScopedMixin


class RolePermission(TenantScopedMixin, Base):
    __tablename__ = "role_permissions"

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "role_id"],
            ["roles.tenant_id", "roles.id"],
            name="fk_role_permissions_tenant_role",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "permission_id"],
            ["permissions.tenant_id", "permissions.id"],
            name="fk_role_permissions_tenant_permission",
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
