"""permite reuso de nome de categoria excluida (unicidade por nome ativo)

Revision ID: b6d4e8f2a1c9
Revises: 7e4b2f9c6a18
Create Date: 2026-10-02 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b6d4e8f2a1c9"
down_revision: str | Sequence[str] | None = "7e4b2f9c6a18"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# A restricao original e uma UNIQUE constraint de tabela
# (sa.UniqueConstraint em b193007ff2be, renomeada por c4a7e29d13b8 e
# 7e4b2f9c6a18), logo e removida com DROP CONSTRAINT.
CONSTRAINT_NAME = "uq_categorias_empresa_name"

# Novo indice parcial: nome unico somente entre categorias ativas
# (deleted_at IS NULL).
INDEX_NAME = "uq_categorias_empresa_name_ativo"


def upgrade() -> None:
    op.drop_constraint(CONSTRAINT_NAME, "categorias", type_="unique")
    op.create_index(
        INDEX_NAME,
        "categorias",
        ["empresa_id", "name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="categorias")
    op.create_unique_constraint(
        CONSTRAINT_NAME,
        "categorias",
        ["empresa_id", "name"],
    )
