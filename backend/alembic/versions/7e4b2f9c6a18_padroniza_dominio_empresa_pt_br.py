"""padroniza identificadores do dominio empresa para pt-br

Revision ID: 7e4b2f9c6a18
Revises: c9d4f1a82b37
Create Date: 2026-10-02 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7e4b2f9c6a18"
down_revision: str | Sequence[str] | None = "c9d4f1a82b37"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Tabelas com a coluna de escopo de empresa (14).
COLUMN_RENAMES: tuple[tuple[str, str, str], ...] = (
    ("audit_logs", "tenant_id", "empresa_id"),
    ("categorias", "tenant_id", "empresa_id"),
    ("clientes", "tenant_id", "empresa_id"),
    ("estoque", "tenant_id", "empresa_id"),
    ("estoque_movimentacoes", "tenant_id", "empresa_id"),
    ("estoque_reservas", "tenant_id", "empresa_id"),
    ("pedido_itens", "tenant_id", "empresa_id"),
    ("pedidos", "tenant_id", "empresa_id"),
    ("permissions", "tenant_id", "empresa_id"),
    ("produtos", "tenant_id", "empresa_id"),
    ("role_permissions", "tenant_id", "empresa_id"),
    ("roles", "tenant_id", "empresa_id"),
    ("user_roles", "tenant_id", "empresa_id"),
    ("users", "tenant_id", "empresa_id"),
)

# Constraints (as unicas e a primary key tambem renomeiam o indice de apoio).
# A tabela tenants ja foi renomeada para empresas no passo 1 do upgrade.
CONSTRAINT_RENAMES: tuple[tuple[str, str, str], ...] = (
    ("empresas", "tenants_pkey", "empresas_pkey"),
    ("empresas", "tenants_slug_key", "empresas_slug_key"),
    ("users", "users_tenant_id_fkey", "users_empresa_id_fkey"),
    ("users", "uq_users_tenant_email", "uq_users_empresa_email"),
    ("users", "uq_users_tenant_id", "uq_users_empresa_id"),
    ("roles", "roles_tenant_id_fkey", "roles_empresa_id_fkey"),
    ("roles", "uq_roles_tenant_id", "uq_roles_empresa_id"),
    ("roles", "uq_roles_tenant_name", "uq_roles_empresa_name"),
    ("permissions", "permissions_tenant_id_fkey", "permissions_empresa_id_fkey"),
    ("permissions", "uq_permissions_tenant_id", "uq_permissions_empresa_id"),
    ("permissions", "uq_permissions_tenant_name", "uq_permissions_empresa_name"),
    ("user_roles", "user_roles_tenant_id_fkey", "user_roles_empresa_id_fkey"),
    ("user_roles", "fk_user_roles_tenant_user", "fk_user_roles_empresa_user"),
    ("user_roles", "fk_user_roles_tenant_role", "fk_user_roles_empresa_role"),
    (
        "role_permissions",
        "role_permissions_tenant_id_fkey",
        "role_permissions_empresa_id_fkey",
    ),
    (
        "role_permissions",
        "fk_role_permissions_tenant_permission",
        "fk_role_permissions_empresa_permission",
    ),
    (
        "role_permissions",
        "fk_role_permissions_tenant_role",
        "fk_role_permissions_empresa_role",
    ),
    ("clientes", "clientes_tenant_id_fkey", "clientes_empresa_id_fkey"),
    ("clientes", "uq_clientes_tenant_document", "uq_clientes_empresa_document"),
    ("clientes", "uq_clientes_tenant_id", "uq_clientes_empresa_id"),
    ("categorias", "categorias_tenant_id_fkey", "categorias_empresa_id_fkey"),
    ("categorias", "fk_categorias_tenant_parent", "fk_categorias_empresa_parent"),
    ("categorias", "uq_categorias_tenant_id", "uq_categorias_empresa_id"),
    ("categorias", "uq_categorias_tenant_name", "uq_categorias_empresa_name"),
    ("produtos", "produtos_tenant_id_fkey", "produtos_empresa_id_fkey"),
    ("produtos", "fk_produtos_tenant_categoria", "fk_produtos_empresa_categoria"),
    ("produtos", "uq_produtos_tenant_id", "uq_produtos_empresa_id"),
    ("produtos", "uq_produtos_tenant_sku", "uq_produtos_empresa_sku"),
    ("estoque", "estoque_tenant_id_fkey", "estoque_empresa_id_fkey"),
    ("estoque", "fk_estoque_tenant_produto", "fk_estoque_empresa_produto"),
    ("estoque", "uq_estoque_tenant_produto", "uq_estoque_empresa_produto"),
    ("pedidos", "pedidos_tenant_id_fkey", "pedidos_empresa_id_fkey"),
    ("pedidos", "fk_pedidos_tenant_cliente", "fk_pedidos_empresa_cliente"),
    ("pedidos", "uq_pedidos_tenant_id", "uq_pedidos_empresa_id"),
    ("pedidos", "uq_pedidos_tenant_numero", "uq_pedidos_empresa_numero"),
    ("pedido_itens", "pedido_itens_tenant_id_fkey", "pedido_itens_empresa_id_fkey"),
    ("pedido_itens", "fk_pedido_itens_tenant_pedido", "fk_pedido_itens_empresa_pedido"),
    (
        "pedido_itens",
        "fk_pedido_itens_tenant_produto",
        "fk_pedido_itens_empresa_produto",
    ),
    (
        "pedido_itens",
        "uq_pedido_itens_tenant_pedido_produto",
        "uq_pedido_itens_empresa_pedido_produto",
    ),
    ("audit_logs", "audit_logs_tenant_id_fkey", "audit_logs_empresa_id_fkey"),
    ("audit_logs", "fk_audit_logs_tenant_user", "fk_audit_logs_empresa_user"),
    (
        "estoque_movimentacoes",
        "estoque_movimentacoes_tenant_id_fkey",
        "estoque_movimentacoes_empresa_id_fkey",
    ),
    (
        "estoque_movimentacoes",
        "estoque_movimentacoes_tenant_id_produto_id_fkey",
        "estoque_movimentacoes_empresa_id_produto_id_fkey",
    ),
    (
        "estoque_movimentacoes",
        "uq_estoque_movimentacoes_tenant_idempotency",
        "uq_estoque_movimentacoes_empresa_idempotency",
    ),
    (
        "estoque_reservas",
        "estoque_reservas_tenant_id_fkey",
        "estoque_reservas_empresa_id_fkey",
    ),
    (
        "estoque_reservas",
        "estoque_reservas_tenant_id_produto_id_fkey",
        "estoque_reservas_empresa_id_produto_id_fkey",
    ),
    (
        "estoque_reservas",
        "uq_estoque_reservas_tenant_idempotency",
        "uq_estoque_reservas_empresa_idempotency",
    ),
)

# Indices simples (coluna/indice proprio, sem constraint de apoio).
INDEX_RENAMES: tuple[tuple[str, str], ...] = (
    ("ix_audit_logs_tenant_id", "ix_audit_logs_empresa_id"),
    ("ix_categorias_tenant_id", "ix_categorias_empresa_id"),
    ("ix_clientes_tenant_id", "ix_clientes_empresa_id"),
    ("ix_estoque_tenant_id", "ix_estoque_empresa_id"),
    ("ix_estoque_movimentacoes_tenant_id", "ix_estoque_movimentacoes_empresa_id"),
    ("ix_estoque_reservas_tenant_id", "ix_estoque_reservas_empresa_id"),
    ("ix_pedido_itens_tenant_id", "ix_pedido_itens_empresa_id"),
    ("ix_pedidos_tenant_id", "ix_pedidos_empresa_id"),
    ("ix_permissions_tenant_id", "ix_permissions_empresa_id"),
    ("ix_produtos_tenant_id", "ix_produtos_empresa_id"),
    ("ix_role_permissions_tenant_id", "ix_role_permissions_empresa_id"),
    ("ix_roles_tenant_id", "ix_roles_empresa_id"),
    ("ix_user_roles_tenant_id", "ix_user_roles_empresa_id"),
    ("ix_users_tenant_id", "ix_users_empresa_id"),
    ("ix_tenants_deleted_at", "ix_empresas_deleted_at"),
    ("ix_tenants_is_active", "ix_empresas_is_active"),
    ("ix_tenants_slug", "ix_empresas_slug"),
)


def upgrade() -> None:
    # 1. Tabela do dominio empresa.
    op.rename_table("tenants", "empresas")

    # 2. Coluna de escopo nas 14 tabelas consumidoras.
    for table, old_column, new_column in COLUMN_RENAMES:
        op.alter_column(table, old_column, new_column_name=new_column)

    # 3. Constraints (SQL explicito: ALTER TABLE ... RENAME CONSTRAINT).
    for table, old_name, new_name in CONSTRAINT_RENAMES:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {old_name} TO {new_name}")

    # 4. Indices (SQL explicito: ALTER INDEX ... RENAME TO).
    for old_name, new_name in INDEX_RENAMES:
        op.execute(f"ALTER INDEX {old_name} RENAME TO {new_name}")

    # 5. Permissoes: nenhuma permission muda de nome (somente o campo de
    #    escopo tenant_id passa a se chamar empresa_id nas tabelas RBAC).
    # 6. Registros historicos de auditoria: nenhuma ocorrencia de tenant em
    #    action, entity_type ou chaves JSONB (levantamento confirmou 0 linhas).
    # 7. Status e enums: o dominio empresa nao possui colunas de status,
    #    portanto nenhum statement e necessario nesta revisao.


def downgrade() -> None:
    # Ordem exata inversa do upgrade.
    for old_name, new_name in INDEX_RENAMES:
        op.execute(f"ALTER INDEX {new_name} RENAME TO {old_name}")

    for table, old_name, new_name in CONSTRAINT_RENAMES:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {new_name} TO {old_name}")

    for table, old_column, new_column in COLUMN_RENAMES:
        op.alter_column(table, new_column, new_column_name=old_column)

    op.rename_table("empresas", "tenants")
