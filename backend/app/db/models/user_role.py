from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKeyConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import EscopoEmpresaMixin


class UserRole(EscopoEmpresaMixin, Base):
    __tablename__ = "user_roles"

    __table_args__ = (
        ForeignKeyConstraint(
            ["empresa_id", "user_id"],
            ["users.empresa_id", "users.id"],
            name="fk_user_roles_empresa_user",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["empresa_id", "role_id"],
            ["roles.empresa_id", "roles.id"],
            name="fk_user_roles_empresa_role",
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
