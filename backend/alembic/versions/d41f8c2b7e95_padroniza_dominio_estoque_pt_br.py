"""padroniza identificadores do dominio estoque para pt-br

Revision ID: d41f8c2b7e95
Revises: b7d4e2a91f5c
Create Date: 2026-10-01 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d41f8c2b7e95"
down_revision: str | Sequence[str] | None = "b7d4e2a91f5c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSION_RENAMES: tuple[tuple[str, str], ...] = (
    ("inventory.read", "estoque.ler"),
    ("inventory.update", "estoque.atualizar"),
)

# Coluna de enum do proprio dominio (values tambem traduzidos mais abaixo).
COLUMN_RENAMES: tuple[tuple[str, str, str], ...] = (
    ("estoque_movimentacoes", "movement_type", "tipo_movimentacao"),
)

# Constraints (as unicas e a primary key tambem renomeiam o indice de apoio).
# A tabela ja foi renomeada: o nome no ALTER TABLE e o novo nome.
CONSTRAINT_RENAMES: tuple[tuple[str, str, str], ...] = (
    ("estoque", "inventory_pkey", "estoque_pkey"),
    ("estoque", "inventory_tenant_id_fkey", "estoque_tenant_id_fkey"),
    ("estoque", "fk_inventory_tenant_produto", "fk_estoque_tenant_produto"),
    ("estoque", "uq_inventory_tenant_produto", "uq_estoque_tenant_produto"),
    ("estoque_movimentacoes", "inventory_movements_pkey", "estoque_movimentacoes_pkey"),
    (
        "estoque_movimentacoes",
        "inventory_movements_tenant_id_fkey",
        "estoque_movimentacoes_tenant_id_fkey",
    ),
    (
        "estoque_movimentacoes",
        "inventory_movements_tenant_id_produto_id_fkey",
        "estoque_movimentacoes_tenant_id_produto_id_fkey",
    ),
    (
        "estoque_movimentacoes",
        "uq_inventory_movements_tenant_idempotency",
        "uq_estoque_movimentacoes_tenant_idempotency",
    ),
    ("estoque_reservas", "inventory_reservations_pkey", "estoque_reservas_pkey"),
    (
        "estoque_reservas",
        "inventory_reservations_tenant_id_fkey",
        "estoque_reservas_tenant_id_fkey",
    ),
    (
        "estoque_reservas",
        "inventory_reservations_tenant_id_produto_id_fkey",
        "estoque_reservas_tenant_id_produto_id_fkey",
    ),
    (
        "estoque_reservas",
        "uq_inventory_reservations_tenant_idempotency",
        "uq_estoque_reservas_tenant_idempotency",
    ),
    (
        "estoque_reservas",
        "fk_inventory_reservations_order_item",
        "fk_estoque_reservas_order_item",
    ),
)

# Indices simples (coluna/indice proprio, sem constraint de apoio).
INDEX_RENAMES: tuple[tuple[str, str], ...] = (
    ("ix_inventory_deleted_at", "ix_estoque_deleted_at"),
    ("ix_inventory_produto_id", "ix_estoque_produto_id"),
    ("ix_inventory_tenant_id", "ix_estoque_tenant_id"),
    (
        "ix_inventory_movements_produto_id",
        "ix_estoque_movimentacoes_produto_id",
    ),
    (
        "ix_inventory_movements_tenant_id",
        "ix_estoque_movimentacoes_tenant_id",
    ),
    (
        "ix_inventory_reservations_order_item_id",
        "ix_estoque_reservas_order_item_id",
    ),
    (
        "ix_inventory_reservations_produto_id",
        "ix_estoque_reservas_produto_id",
    ),
    (
        "ix_inventory_reservations_tenant_id",
        "ix_estoque_reservas_tenant_id",
    ),
)

# Valores dos enums do dominio (varchar, sem constraint CHECK).
MOVEMENT_TYPE_VALUES: tuple[tuple[str, str], ...] = (
    ("IN", "ENTRADA"),
    ("OUT", "SAIDA"),
    ("ADJUSTMENT", "AJUSTE"),
)

RESERVATION_STATUS_VALUES: tuple[tuple[str, str], ...] = (
    ("ACTIVE", "ATIVA"),
    ("CONFIRMED", "CONFIRMADA"),
    ("RELEASED", "LIBERADA"),
    ("CANCELLED", "CANCELADA"),
)

AUDIT_ACTIONS: tuple[tuple[str, str], ...] = (
    ("INVENTORY_IN", "ESTOQUE_ENTRADA"),
    ("INVENTORY_OUT", "ESTOQUE_SAIDA"),
    ("INVENTORY_ADJUSTMENT", "ESTOQUE_AJUSTE"),
    ("RESERVATION_CREATE", "RESERVA_CRIAR"),
    ("RESERVATION_CONFIRM", "RESERVA_CONFIRMAR"),
    ("RESERVATION_RELEASE", "RESERVA_LIBERAR"),
    ("RESERVATION_CANCEL", "RESERVA_CANCELAR"),
)

AUDIT_ENTITY_TYPES: tuple[tuple[str, str], ...] = (
    ("inventory", "estoque"),
    ("inventory_reservation", "reserva"),
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


def upgrade() -> None:
    # 1. Tabelas do dominio estoque.
    op.rename_table("inventory", "estoque")
    op.rename_table("inventory_movements", "estoque_movimentacoes")
    op.rename_table("inventory_reservations", "estoque_reservas")

    # 2. Coluna de enum do dominio.
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
    _rename_audit(AUDIT_ACTIONS, "action")
    _rename_audit(AUDIT_ENTITY_TYPES, "entity_type")

    # 7. Valores dos enums de movimentacao e de reserva.
    _rename_values("estoque_movimentacoes", "tipo_movimentacao", MOVEMENT_TYPE_VALUES)
    _rename_values("estoque_reservas", "status", RESERVATION_STATUS_VALUES)


def downgrade() -> None:
    # Ordem exata inversa do upgrade.
    _rename_values(
        "estoque_reservas",
        "status",
        tuple(
            (new_value, old_value) for old_value, new_value in RESERVATION_STATUS_VALUES
        ),
    )
    _rename_values(
        "estoque_movimentacoes",
        "tipo_movimentacao",
        tuple((new_value, old_value) for old_value, new_value in MOVEMENT_TYPE_VALUES),
    )

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

    for old_name, new_name in INDEX_RENAMES:
        op.execute(f"ALTER INDEX {new_name} RENAME TO {old_name}")

    for table, old_name, new_name in CONSTRAINT_RENAMES:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {new_name} TO {old_name}")

    for table, old_column, new_column in COLUMN_RENAMES:
        op.alter_column(table, new_column, new_column_name=old_column)

    op.rename_table("estoque_reservas", "inventory_reservations")
    op.rename_table("estoque_movimentacoes", "inventory_movements")
    op.rename_table("estoque", "inventory")
