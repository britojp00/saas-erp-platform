"""padroniza identificadores do dominio produto para pt-br

Revision ID: b7d4e2a91f5c
Revises: c4a7e29d13b8
Create Date: 2026-09-29 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7d4e2a91f5c"
down_revision: str | Sequence[str] | None = "c4a7e29d13b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSION_RENAMES: tuple[tuple[str, str], ...] = (
    ("product.read", "produto.ler"),
    ("product.create", "produto.criar"),
    ("product.update", "produto.atualizar"),
    ("product.delete", "produto.excluir"),
)

# Colunas product_id de outras tabelas apontando para o produto.
COLUMN_RENAMES: tuple[tuple[str, str, str], ...] = (
    ("inventory", "product_id", "produto_id"),
    ("inventory_movements", "product_id", "produto_id"),
    ("inventory_reservations", "product_id", "produto_id"),
    ("order_items", "product_id", "produto_id"),
)

# Constraints (as unicas e a primary key tambem renomeiam o indice de apoio).
CONSTRAINT_RENAMES: tuple[tuple[str, str, str], ...] = (
    ("produtos", "products_pkey", "produtos_pkey"),
    ("produtos", "products_tenant_id_fkey", "produtos_tenant_id_fkey"),
    ("produtos", "fk_products_tenant_categoria", "fk_produtos_tenant_categoria"),
    ("produtos", "uq_products_tenant_id", "uq_produtos_tenant_id"),
    ("produtos", "uq_products_tenant_sku", "uq_produtos_tenant_sku"),
    ("inventory", "fk_inventory_tenant_product", "fk_inventory_tenant_produto"),
    ("inventory", "uq_inventory_tenant_product", "uq_inventory_tenant_produto"),
    (
        "inventory_movements",
        "inventory_movements_tenant_id_product_id_fkey",
        "inventory_movements_tenant_id_produto_id_fkey",
    ),
    (
        "inventory_reservations",
        "inventory_reservations_tenant_id_product_id_fkey",
        "inventory_reservations_tenant_id_produto_id_fkey",
    ),
    ("order_items", "fk_order_items_tenant_product", "fk_order_items_tenant_produto"),
    (
        "order_items",
        "uq_order_items_tenant_order_product",
        "uq_order_items_tenant_order_produto",
    ),
)

# Indices simples (coluna/indice proprio, sem constraint de apoio).
INDEX_RENAMES: tuple[tuple[str, str], ...] = (
    ("ix_products_categoria_id", "ix_produtos_categoria_id"),
    ("ix_products_deleted_at", "ix_produtos_deleted_at"),
    ("ix_products_is_active", "ix_produtos_is_active"),
    ("ix_products_tenant_id", "ix_produtos_tenant_id"),
    ("ix_inventory_product_id", "ix_inventory_produto_id"),
    ("ix_inventory_movements_product_id", "ix_inventory_movements_produto_id"),
    (
        "ix_inventory_reservations_product_id",
        "ix_inventory_reservations_produto_id",
    ),
    ("ix_order_items_product_id", "ix_order_items_produto_id"),
)


def upgrade() -> None:
    # 1. Tabela do dominio produto.
    op.rename_table("products", "produtos")

    # 2. Referencia do dominio produto dentro de inventory e order_items.
    for table, old_column, new_column in COLUMN_RENAMES:
        op.alter_column(table, old_column, new_column_name=new_column)

    # 3. Constraints (SQL explicito: ALTER TABLE ... RENAME CONSTRAINT).
    for table, old_name, new_name in CONSTRAINT_RENAMES:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {old_name} TO {new_name}")

    # 4. Indices.
    for old_name, new_name in INDEX_RENAMES:
        op.execute(f"ALTER INDEX {old_name} RENAME TO {new_name}")

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
                        WHEN 'PRODUCT_CREATE' THEN 'PRODUTO_CRIAR'
                        WHEN 'PRODUCT_UPDATE' THEN 'PRODUTO_ATUALIZAR'
                        WHEN 'PRODUCT_DELETE' THEN 'PRODUTO_EXCLUIR'
                        ELSE action
                      END,
            entity_type = CASE
                            WHEN entity_type = 'product' THEN 'produto'
                            ELSE entity_type
                          END
        WHERE action IN ('PRODUCT_CREATE', 'PRODUCT_UPDATE', 'PRODUCT_DELETE')
           OR entity_type = 'product'
        """
    )

    # 7. Status e enums: o dominio produto nao possui colunas de status
    #    (apenas is_active boolean), portanto nenhum statement e necessario.


def downgrade() -> None:
    # Ordem exata inversa do upgrade.
    op.execute(
        """
        UPDATE audit_logs
        SET action = CASE action
                        WHEN 'PRODUTO_CRIAR' THEN 'PRODUCT_CREATE'
                        WHEN 'PRODUTO_ATUALIZAR' THEN 'PRODUCT_UPDATE'
                        WHEN 'PRODUTO_EXCLUIR' THEN 'PRODUCT_DELETE'
                        ELSE action
                      END,
            entity_type = CASE
                            WHEN entity_type = 'produto' THEN 'product'
                            ELSE entity_type
                          END
        WHERE action IN ('PRODUTO_CRIAR', 'PRODUTO_ATUALIZAR', 'PRODUTO_EXCLUIR')
           OR entity_type = 'produto'
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

    for old_name, new_name in INDEX_RENAMES:
        op.execute(f"ALTER INDEX {new_name} RENAME TO {old_name}")

    for table, old_name, new_name in CONSTRAINT_RENAMES:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {new_name} TO {old_name}")

    for table, old_column, new_column in COLUMN_RENAMES:
        op.alter_column(table, new_column, new_column_name=old_column)

    op.rename_table("produtos", "products")
