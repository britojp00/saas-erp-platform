"""padroniza identificadores do dominio categoria para pt-br

Revision ID: c4a7e29d13b8
Revises: 0a989f3b384b
Create Date: 2026-09-29 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4a7e29d13b8"
down_revision: str | Sequence[str] | None = "0a989f3b384b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSION_RENAMES: tuple[tuple[str, str], ...] = (
    ("category.read", "categoria.ler"),
    ("category.create", "categoria.criar"),
    ("category.update", "categoria.atualizar"),
    ("category.delete", "categoria.excluir"),
)


def upgrade() -> None:
    # 1. Tabela do dominio categoria.
    op.rename_table("categories", "categorias")

    # 2. Referencia do dominio categoria dentro da estrutura de produtos.
    op.alter_column("products", "category_id", new_column_name="categoria_id")

    # 3. Constraints (SQL explicito: ALTER TABLE ... RENAME CONSTRAINT).
    op.execute(
        "ALTER TABLE categorias RENAME CONSTRAINT categories_pkey TO categorias_pkey"
    )
    op.execute(
        "ALTER TABLE categorias RENAME CONSTRAINT categories_tenant_id_fkey "
        "TO categorias_tenant_id_fkey"
    )
    op.execute(
        "ALTER TABLE categorias RENAME CONSTRAINT uq_categories_tenant_name "
        "TO uq_categorias_tenant_name"
    )
    op.execute(
        "ALTER TABLE categorias RENAME CONSTRAINT uq_categories_tenant_id "
        "TO uq_categorias_tenant_id"
    )
    op.execute(
        "ALTER TABLE categorias RENAME CONSTRAINT fk_categories_tenant_parent "
        "TO fk_categorias_tenant_parent"
    )
    op.execute(
        "ALTER TABLE products RENAME CONSTRAINT fk_products_tenant_category "
        "TO fk_products_tenant_categoria"
    )

    # 4. Indices.
    op.execute(
        "ALTER INDEX ix_categories_deleted_at RENAME TO ix_categorias_deleted_at"
    )
    op.execute("ALTER INDEX ix_categories_parent_id RENAME TO ix_categorias_parent_id")
    op.execute("ALTER INDEX ix_categories_tenant_id RENAME TO ix_categorias_tenant_id")
    op.execute("ALTER INDEX ix_products_category_id RENAME TO ix_products_categoria_id")

    # 5. Permissoes (guard anti-conflito com uq_permissions_tenant_name).
    for old_name, new_name in PERMISSION_RENAMES:
        op.execute(
            f"""
            UPDATE permissions
            SET name = '{new_name}'
            WHERE name = '{old_name}'
              AND NOT EXISTS (
                    SELECT 1
                    FROM permissions p
                    WHERE p.name = '{new_name}'
                      AND p.tenant_id IS NOT DISTINCT FROM permissions.tenant_id
              )
            """
        )

    # 6. Registros historicos de auditoria (actions e entity_type).
    #    Chaves JSONB nao sao alteradas: levantamento confirmou 0 ocorrencias.
    op.execute(
        """
        UPDATE audit_logs
        SET action = CASE action
                        WHEN 'CATEGORY_CREATE' THEN 'CATEGORIA_CRIAR'
                        WHEN 'CATEGORY_UPDATE' THEN 'CATEGORIA_ATUALIZAR'
                        WHEN 'CATEGORY_DELETE' THEN 'CATEGORIA_EXCLUIR'
                        ELSE action
                      END,
            entity_type = CASE
                            WHEN entity_type = 'category' THEN 'categoria'
                            ELSE entity_type
                          END
        WHERE action IN ('CATEGORY_CREATE', 'CATEGORY_UPDATE', 'CATEGORY_DELETE')
           OR entity_type = 'category'
        """
    )

    # 7. Status e enums: o dominio categoria nao possui colunas de status,
    #    portanto nenhum statement e necessario nesta revisao.


def downgrade() -> None:
    # Ordem exata inversa do upgrade.
    op.execute(
        """
        UPDATE audit_logs
        SET action = CASE action
                        WHEN 'CATEGORIA_CRIAR' THEN 'CATEGORY_CREATE'
                        WHEN 'CATEGORIA_ATUALIZAR' THEN 'CATEGORY_UPDATE'
                        WHEN 'CATEGORIA_EXCLUIR' THEN 'CATEGORY_DELETE'
                        ELSE action
                      END,
            entity_type = CASE
                            WHEN entity_type = 'categoria' THEN 'category'
                            ELSE entity_type
                          END
        WHERE action IN ('CATEGORIA_CRIAR', 'CATEGORIA_ATUALIZAR', 'CATEGORIA_EXCLUIR')
           OR entity_type = 'categoria'
        """
    )

    for old_name, new_name in PERMISSION_RENAMES:
        op.execute(
            f"""
            UPDATE permissions
            SET name = '{old_name}'
            WHERE name = '{new_name}'
              AND NOT EXISTS (
                    SELECT 1
                    FROM permissions p
                    WHERE p.name = '{old_name}'
                      AND p.tenant_id IS NOT DISTINCT FROM permissions.tenant_id
              )
            """
        )

    op.execute("ALTER INDEX ix_products_categoria_id RENAME TO ix_products_category_id")
    op.execute("ALTER INDEX ix_categorias_tenant_id RENAME TO ix_categories_tenant_id")
    op.execute("ALTER INDEX ix_categorias_parent_id RENAME TO ix_categories_parent_id")
    op.execute(
        "ALTER INDEX ix_categorias_deleted_at RENAME TO ix_categories_deleted_at"
    )

    op.execute(
        "ALTER TABLE products RENAME CONSTRAINT fk_products_tenant_categoria "
        "TO fk_products_tenant_category"
    )
    op.execute(
        "ALTER TABLE categorias RENAME CONSTRAINT fk_categorias_tenant_parent "
        "TO fk_categories_tenant_parent"
    )
    op.execute(
        "ALTER TABLE categorias RENAME CONSTRAINT uq_categorias_tenant_id "
        "TO uq_categories_tenant_id"
    )
    op.execute(
        "ALTER TABLE categorias RENAME CONSTRAINT uq_categorias_tenant_name "
        "TO uq_categories_tenant_name"
    )
    op.execute(
        "ALTER TABLE categorias RENAME CONSTRAINT categorias_tenant_id_fkey "
        "TO categories_tenant_id_fkey"
    )
    op.execute(
        "ALTER TABLE categorias RENAME CONSTRAINT categorias_pkey TO categories_pkey"
    )

    op.alter_column("products", "categoria_id", new_column_name="category_id")

    op.rename_table("categorias", "categories")
