"""padroniza identificadores do dominio cliente para pt-br

Revision ID: 0a989f3b384b
Revises: a6e3de570b07
Create Date: 2026-09-29 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0a989f3b384b"
down_revision: str | Sequence[str] | None = "a6e3de570b07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSION_RENAMES: tuple[tuple[str, str], ...] = (
    ("customer.read", "cliente.ler"),
    ("customer.create", "cliente.criar"),
    ("customer.update", "cliente.atualizar"),
    ("customer.delete", "cliente.excluir"),
)


def upgrade() -> None:
    # 1. Tabela do dominio cliente.
    op.rename_table("customers", "clientes")

    # 2. Referencia do dominio cliente dentro da estrutura de pedidos.
    op.alter_column("orders", "customer_id", new_column_name="cliente_id")

    # 3. Constraints (SQL explicito: ALTER TABLE ... RENAME CONSTRAINT).
    op.execute("ALTER TABLE clientes RENAME CONSTRAINT customers_pkey TO clientes_pkey")
    op.execute(
        "ALTER TABLE clientes RENAME CONSTRAINT customers_tenant_id_fkey "
        "TO clientes_tenant_id_fkey"
    )
    op.execute(
        "ALTER TABLE clientes RENAME CONSTRAINT uq_customers_tenant_document "
        "TO uq_clientes_tenant_document"
    )
    op.execute(
        "ALTER TABLE clientes RENAME CONSTRAINT uq_customers_tenant_id "
        "TO uq_clientes_tenant_id"
    )
    op.execute(
        "ALTER TABLE orders RENAME CONSTRAINT fk_orders_tenant_customer "
        "TO fk_orders_tenant_cliente"
    )

    # 4. Indices.
    op.execute("ALTER INDEX ix_customers_deleted_at RENAME TO ix_clientes_deleted_at")
    op.execute("ALTER INDEX ix_customers_tenant_id RENAME TO ix_clientes_tenant_id")
    op.execute("ALTER INDEX ix_orders_customer_id RENAME TO ix_orders_cliente_id")

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
                        WHEN 'CUSTOMER_CREATE' THEN 'CLIENTE_CRIAR'
                        WHEN 'CUSTOMER_UPDATE' THEN 'CLIENTE_ATUALIZAR'
                        WHEN 'CUSTOMER_DELETE' THEN 'CLIENTE_EXCLUIR'
                        ELSE action
                      END,
            entity_type = CASE
                            WHEN entity_type = 'customer' THEN 'cliente'
                            ELSE entity_type
                          END
        WHERE action IN ('CUSTOMER_CREATE', 'CUSTOMER_UPDATE', 'CUSTOMER_DELETE')
           OR entity_type = 'customer'
        """
    )

    # 7. Status e enums: o dominio cliente nao possui colunas de status,
    #    portanto nenhum statement e necessario nesta revisao.


def downgrade() -> None:
    # Ordem exata inversa do upgrade.
    op.execute(
        """
        UPDATE audit_logs
        SET action = CASE action
                        WHEN 'CLIENTE_CRIAR' THEN 'CUSTOMER_CREATE'
                        WHEN 'CLIENTE_ATUALIZAR' THEN 'CUSTOMER_UPDATE'
                        WHEN 'CLIENTE_EXCLUIR' THEN 'CUSTOMER_DELETE'
                        ELSE action
                      END,
            entity_type = CASE
                            WHEN entity_type = 'cliente' THEN 'customer'
                            ELSE entity_type
                          END
        WHERE action IN ('CLIENTE_CRIAR', 'CLIENTE_ATUALIZAR', 'CLIENTE_EXCLUIR')
           OR entity_type = 'cliente'
        """
    )

    for new_name, old_name in PERMISSION_RENAMES:
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

    op.execute("ALTER INDEX ix_orders_cliente_id RENAME TO ix_orders_customer_id")
    op.execute("ALTER INDEX ix_clientes_tenant_id RENAME TO ix_customers_tenant_id")
    op.execute("ALTER INDEX ix_clientes_deleted_at RENAME TO ix_customers_deleted_at")
    op.execute(
        "ALTER TABLE orders RENAME CONSTRAINT fk_orders_tenant_cliente "
        "TO fk_orders_tenant_customer"
    )
    op.execute(
        "ALTER TABLE clientes RENAME CONSTRAINT uq_clientes_tenant_id "
        "TO uq_customers_tenant_id"
    )
    op.execute(
        "ALTER TABLE clientes RENAME CONSTRAINT uq_clientes_tenant_document "
        "TO uq_customers_tenant_document"
    )
    op.execute(
        "ALTER TABLE clientes RENAME CONSTRAINT clientes_tenant_id_fkey "
        "TO customers_tenant_id_fkey"
    )
    op.execute("ALTER TABLE clientes RENAME CONSTRAINT clientes_pkey TO customers_pkey")

    op.alter_column("orders", "cliente_id", new_column_name="customer_id")

    op.rename_table("clientes", "customers")
