from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKeyConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TenantScopedMixin


class UserRole(TenantScopedMixin, Base):
    __tablename__ = "user_roles"

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_user_roles_tenant_user",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "role_id"],
            ["roles.tenant_id", "roles.id"],
            name="fk_user_roles_tenant_role",
            ondelete="CASCADE",
        ),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    role_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
