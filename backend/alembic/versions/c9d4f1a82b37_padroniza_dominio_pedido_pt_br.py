"""padroniza identificadores do dominio pedido para pt-br

Revision ID: c9d4f1a82b37
Revises: d41f8c2b7e95
Create Date: 2026-10-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9d4f1a82b37"
down_revision: str | Sequence[str] | None = "d41f8c2b7e95"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSION_RENAMES: tuple[tuple[str, str], ...] = (
    ("order.read", "pedido.ler"),
    ("order.create", "pedido.criar"),
    ("order.update", "pedido.atualizar"),
    ("order.cancel", "pedido.cancelar"),
)

# Colunas proprias do dominio (inclui a referencia cross-domain em
# estoque_reservas, renomeada conforme decisao D12).
COLUMN_RENAMES: tuple[tuple[str, str, str], ...] = (
    ("pedidos", "order_number", "numero_pedido"),
    ("pedido_itens", "order_id", "pedido_id"),
    ("estoque_reservas", "order_item_id", "pedido_item_id"),
)

# Constraints (as unicas e a primary key tambem renomeiam o indice de apoio).
# As tabelas ja foram renomeadas: o nome no ALTER TABLE e o novo nome.
CONSTRAINT_RENAMES: tuple[tuple[str, str, str], ...] = (
    ("pedidos", "orders_pkey", "pedidos_pkey"),
    ("pedidos", "orders_tenant_id_fkey", "pedidos_tenant_id_fkey"),
    ("pedidos", "fk_orders_tenant_cliente", "fk_pedidos_tenant_cliente"),
    ("pedidos", "uq_orders_tenant_id", "uq_pedidos_tenant_id"),
    ("pedidos", "uq_orders_tenant_number", "uq_pedidos_tenant_numero"),
    ("pedido_itens", "order_items_pkey", "pedido_itens_pkey"),
    ("pedido_itens", "order_items_tenant_id_fkey", "pedido_itens_tenant_id_fkey"),
    (
        "pedido_itens",
        "fk_order_items_tenant_order",
        "fk_pedido_itens_tenant_pedido",
    ),
    (
        "pedido_itens",
        "fk_order_items_tenant_produto",
        "fk_pedido_itens_tenant_produto",
    ),
    (
        "pedido_itens",
        "uq_order_items_tenant_order_produto",
        "uq_pedido_itens_tenant_pedido_produto",
    ),
    (
        "estoque_reservas",
        "fk_estoque_reservas_order_item",
        "fk_estoque_reservas_pedido_item",
    ),
)

# Indices simples (coluna/indice proprio, sem constraint de apoio).
INDEX_RENAMES: tuple[tuple[str, str], ...] = (
    ("ix_orders_cliente_id", "ix_pedidos_cliente_id"),
    ("ix_orders_deleted_at", "ix_pedidos_deleted_at"),
    ("ix_orders_status", "ix_pedidos_status"),
    ("ix_orders_tenant_id", "ix_pedidos_tenant_id"),
    ("ix_order_items_order_id", "ix_pedido_itens_pedido_id"),
    ("ix_order_items_produto_id", "ix_pedido_itens_produto_id"),
    ("ix_order_items_tenant_id", "ix_pedido_itens_tenant_id"),
    (
        "ix_estoque_reservas_order_item_id",
        "ix_estoque_reservas_pedido_item_id",
    ),
)

# Valores do status do dominio (varchar, sem constraint CHECK).
STATUS_VALUES: tuple[tuple[str, str], ...] = (
    ("DRAFT", "RASCUNHO"),
    ("CONFIRMED", "CONFIRMADO"),
    ("COMPLETED", "CONCLUIDO"),
    ("CANCELLED", "CANCELADO"),
)

AUDIT_ACTIONS: tuple[tuple[str, str], ...] = (
    ("ORDER_CREATE", "PEDIDO_CRIAR"),
    ("ORDER_UPDATE", "PEDIDO_ATUALIZAR"),
    ("ORDER_CONFIRM", "PEDIDO_CONFIRMAR"),
    ("ORDER_CANCEL", "PEDIDO_CANCELAR"),
    ("ORDER_COMPLETE", "PEDIDO_CONCLUIR"),
    ("ORDER_ITEM_ADD", "PEDIDO_ITEM_ADICIONAR"),
    ("ORDER_ITEM_UPDATE", "PEDIDO_ITEM_ATUALIZAR"),
    ("ORDER_ITEM_REMOVE", "PEDIDO_ITEM_REMOVER"),
)

AUDIT_ENTITY_TYPES: tuple[tuple[str, str], ...] = (
    ("order", "pedido"),
    ("order_item", "pedido_item"),
)

# Formato dos dados de estoque_reservas (0 linhas no ambiente de dev;
# UPDATE com WHERE explicito para outros ambientes).
REFERENCE_PREFIX_RENAMES: tuple[tuple[str, str], ...] = (
    ("reference", "order:", "pedido:"),
    ("idempotency_key", "order:", "pedido:"),
)


def _rename_values(
    table: str, column: str, renames: tuple[tuple[str, str], ...]
) -> None:
    for old_value, new_value in renames:
        op.execute(
            f"UPDATE {table} SET {column} = '{new_value}' "
            f"WHERE {column} = '{old_value}'"
        )


def _rename_audit(renames: tuple[tuple[str, str], ...], column: str) -> None:
    cases = "\n".join(
        f"WHEN '{old_value}' THEN '{new_value}'" for old_value, new_value in renames
    )
    in_list = ", ".join(f"'{old_value}'" for old_value, _ in renames)
    op.execute(
        f"""
        UPDATE audit_logs
        SET {column} = CASE {column}
                        {cases}
                        ELSE {column}
                      END
        WHERE {column} IN ({in_list})
        """
    )


def _rename_reference_prefixes(reverse: bool = False) -> None:
    for column, old_prefix, new_prefix in REFERENCE_PREFIX_RENAMES:
        source_prefix, target_prefix = old_prefix, new_prefix
        if reverse:
            source_prefix, target_prefix = new_prefix, old_prefix
        op.execute(
            f"""
            UPDATE estoque_reservas
            SET {column} = '{target_prefix}' || substr({column}, {len(source_prefix) + 1})
            WHERE {column} LIKE '{source_prefix}%'
            """
        )


def upgrade() -> None:
    # 1. Tabelas do dominio pedido.
    op.rename_table("orders", "pedidos")
    op.rename_table("order_items", "pedido_itens")

    # 2. Colunas proprias (inclui a cross-domain em estoque_reservas).
    for table, old_column, new_column in COLUMN_RENAMES:
        op.alter_column(table, old_column, new_column_name=new_column)

    # 3. Constraints (SQL explicito: ALTER TABLE ... RENAME CONSTRAINT).
    for table, old_name, new_name in CONSTRAINT_RENAMES:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {old_name} TO {new_name}")

    # 4. Indices.
    for old_name, new_name in INDEX_RENAMES:
        op.execute(f"ALTER INDEX {old_name} RENAME TO {new_name}")

    # 5. Server default da coluna de status.
    op.alter_column(
        "pedidos",
        "status",
        existing_type=sa.String(30),
        server_default=sa.text("'RASCUNHO'"),
    )

    # 6. Valores do status (5 linhas no ambiente de dev).
    _rename_values("pedidos", "status", STATUS_VALUES)

    # 7. Permissoes (guard anti-conflito com uq_permissions_tenant_name).
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

    # 8. Registros historicos de auditoria (actions e entity_type).
    #    Chaves JSONB nao sao alteradas: levantamento confirmou 0 ocorrencias.
    _rename_audit(AUDIT_ACTIONS, "action")
    _rename_audit(AUDIT_ENTITY_TYPES, "entity_type")

    # 9. Formato dos dados de estoque_reservas (reference/idempotency_key).
    _rename_reference_prefixes()


def downgrade() -> None:
    # Ordem exata inversa do upgrade.
    _rename_reference_prefixes(reverse=True)

    _rename_audit(
        tuple((new_value, old_value) for old_value, new_value in AUDIT_ENTITY_TYPES),
        "entity_type",
    )
    _rename_audit(
        tuple((new_value, old_value) for old_value, new_value in AUDIT_ACTIONS),
        "action",
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

    _rename_values(
        "pedidos",
        "status",
        tuple((new_value, old_value) for old_value, new_value in STATUS_VALUES),
    )

    op.alter_column(
        "pedidos",
        "status",
        existing_type=sa.String(30),
        server_default=sa.text("'DRAFT'"),
    )

    for old_name, new_name in INDEX_RENAMES:
        op.execute(f"ALTER INDEX {new_name} RENAME TO {old_name}")

    for table, old_name, new_name in CONSTRAINT_RENAMES:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {new_name} TO {old_name}")

    for table, old_column, new_column in COLUMN_RENAMES:
        op.alter_column(table, new_column, new_column_name=old_column)

    op.rename_table("pedido_itens", "order_items")
    op.rename_table("pedidos", "orders")
