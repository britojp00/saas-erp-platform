"""migrate uuid to bigint

Revision ID: b193007ff2be
Revises: f85b2840792a
Create Date: 2026-09-18 23:13:00.785960

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b193007ff2be"
down_revision: str | Sequence[str] | None = "f85b2840792a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop all tables in FK-dependency order.
    op.execute("DROP TABLE IF EXISTS order_items CASCADE")
    op.execute("DROP TABLE IF EXISTS inventory CASCADE")
    op.execute("DROP TABLE IF EXISTS orders CASCADE")
    op.execute("DROP TABLE IF EXISTS products CASCADE")
    op.execute("DROP TABLE IF EXISTS audit_logs CASCADE")
    op.execute("DROP TABLE IF EXISTS categories CASCADE")
    op.execute("DROP TABLE IF EXISTS customers CASCADE")
    op.execute("DROP TABLE IF EXISTS role_permissions CASCADE")
    op.execute("DROP TABLE IF EXISTS user_roles CASCADE")
    op.execute("DROP TABLE IF EXISTS permissions CASCADE")
    op.execute("DROP TABLE IF EXISTS roles CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TABLE IF EXISTS tenants CASCADE")

    # Create tenants
    op.create_table(
        "tenants",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_tenants_deleted_at", "tenants", ["deleted_at"])
    op.create_index("ix_tenants_is_active", "tenants", ["is_active"])
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    # Create users
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "tenant_id",
            sa.BigInteger,
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_users_tenant_id"),
    )
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])
    op.create_index("ix_users_is_active", "users", ["is_active"])
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])

    # Create roles
    op.create_table(
        "roles",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "tenant_id",
            sa.BigInteger,
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_roles_tenant_id"),
    )
    op.create_index("ix_roles_deleted_at", "roles", ["deleted_at"])
    op.create_index("ix_roles_tenant_id", "roles", ["tenant_id"])

    # Create permissions
    op.create_table(
        "permissions",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "tenant_id",
            sa.BigInteger,
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "name", name="uq_permissions_tenant_name"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_permissions_tenant_id"),
    )
    op.create_index("ix_permissions_deleted_at", "permissions", ["deleted_at"])
    op.create_index("ix_permissions_tenant_id", "permissions", ["tenant_id"])

    # Create user_roles
    op.create_table(
        "user_roles",
        sa.Column(
            "tenant_id",
            sa.BigInteger,
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("user_id", sa.BigInteger, primary_key=True),
        sa.Column("role_id", sa.BigInteger, primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_user_roles_tenant_user",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "role_id"],
            ["roles.tenant_id", "roles.id"],
            name="fk_user_roles_tenant_role",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_user_roles_tenant_id", "user_roles", ["tenant_id"])

    # Create role_permissions
    op.create_table(
        "role_permissions",
        sa.Column(
            "tenant_id",
            sa.BigInteger,
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("role_id", sa.BigInteger, primary_key=True),
        sa.Column("permission_id", sa.BigInteger, primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "role_id"],
            ["roles.tenant_id", "roles.id"],
            name="fk_role_permissions_tenant_role",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "permission_id"],
            ["permissions.tenant_id", "permissions.id"],
            name="fk_role_permissions_tenant_permission",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_role_permissions_tenant_id", "role_permissions", ["tenant_id"])

    # Create customers
    op.create_table(
        "customers",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("document", sa.String(30), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "tenant_id",
            sa.BigInteger,
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "tenant_id", "document", name="uq_customers_tenant_document"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_customers_tenant_id"),
    )
    op.create_index("ix_customers_deleted_at", "customers", ["deleted_at"])
    op.create_index("ix_customers_tenant_id", "customers", ["tenant_id"])

    # Create categories
    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("parent_id", sa.BigInteger, nullable=True),
        sa.Column(
            "tenant_id",
            sa.BigInteger,
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id", "parent_id"],
            ["categories.tenant_id", "categories.id"],
            name="fk_categories_tenant_parent",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("tenant_id", "name", name="uq_categories_tenant_name"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_categories_tenant_id"),
    )
    op.create_index("ix_categories_deleted_at", "categories", ["deleted_at"])
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])
    op.create_index("ix_categories_tenant_id", "categories", ["tenant_id"])

    # Create products
    op.create_table(
        "products",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("sku", sa.String(50), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category_id", sa.BigInteger, nullable=True),
        sa.Column("price", sa.Numeric(15, 2), nullable=False),
        sa.Column("cost_price", sa.Numeric(15, 2), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "tenant_id",
            sa.BigInteger,
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id", "category_id"],
            ["categories.tenant_id", "categories.id"],
            name="fk_products_tenant_category",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("tenant_id", "sku", name="uq_products_tenant_sku"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_products_tenant_id"),
    )
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index("ix_products_deleted_at", "products", ["deleted_at"])
    op.create_index("ix_products_is_active", "products", ["is_active"])
    op.create_index("ix_products_tenant_id", "products", ["tenant_id"])

    # Create inventory
    op.create_table(
        "inventory",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("product_id", sa.BigInteger, nullable=False),
        sa.Column("quantity", sa.Numeric(15, 3), server_default="0", nullable=False),
        sa.Column(
            "reserved_quantity", sa.Numeric(15, 3), server_default="0", nullable=False
        ),
        sa.Column(
            "tenant_id",
            sa.BigInteger,
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id", "product_id"],
            ["products.tenant_id", "products.id"],
            name="fk_inventory_tenant_product",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "tenant_id", "product_id", name="uq_inventory_tenant_product"
        ),
    )
    op.create_index("ix_inventory_deleted_at", "inventory", ["deleted_at"])
    op.create_index("ix_inventory_product_id", "inventory", ["product_id"])
    op.create_index("ix_inventory_tenant_id", "inventory", ["tenant_id"])

    # Create orders
    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("order_number", sa.String(50), nullable=False),
        sa.Column("customer_id", sa.BigInteger, nullable=True),
        sa.Column(
            "status",
            sa.String(30),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "total_amount",
            sa.Numeric(15, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.BigInteger,
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["customers.tenant_id", "customers.id"],
            name="fk_orders_tenant_customer",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "tenant_id", "order_number", name="uq_orders_tenant_number"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_orders_tenant_id"),
    )
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])
    op.create_index("ix_orders_deleted_at", "orders", ["deleted_at"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_tenant_id", "orders", ["tenant_id"])

    # Create order_items
    op.create_table(
        "order_items",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("order_id", sa.BigInteger, nullable=False),
        sa.Column("product_id", sa.BigInteger, nullable=False),
        sa.Column("quantity", sa.Numeric(15, 3), nullable=False),
        sa.Column("unit_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("total_price", sa.Numeric(15, 2), nullable=False),
        sa.Column(
            "tenant_id",
            sa.BigInteger,
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "order_id"],
            ["orders.tenant_id", "orders.id"],
            name="fk_order_items_tenant_order",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "product_id"],
            ["products.tenant_id", "products.id"],
            name="fk_order_items_tenant_product",
            ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])
    op.create_index("ix_order_items_product_id", "order_items", ["product_id"])
    op.create_index("ix_order_items_tenant_id", "order_items", ["tenant_id"])

    # Create audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("user_id", sa.BigInteger, nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.BigInteger, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("old_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.BigInteger,
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_audit_logs_tenant_user",
            ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS order_items CASCADE")
    op.execute("DROP TABLE IF EXISTS inventory CASCADE")
    op.execute("DROP TABLE IF EXISTS orders CASCADE")
    op.execute("DROP TABLE IF EXISTS products CASCADE")
    op.execute("DROP TABLE IF EXISTS audit_logs CASCADE")
    op.execute("DROP TABLE IF EXISTS categories CASCADE")
    op.execute("DROP TABLE IF EXISTS customers CASCADE")
    op.execute("DROP TABLE IF EXISTS role_permissions CASCADE")
    op.execute("DROP TABLE IF EXISTS user_roles CASCADE")
    op.execute("DROP TABLE IF EXISTS permissions CASCADE")
    op.execute("DROP TABLE IF EXISTS roles CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TABLE IF EXISTS tenants CASCADE")
