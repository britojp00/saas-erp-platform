"""orders_module_order_number_bigint_order_items_unique_inventory_reservation_order_item

Revision ID: 198c8c108788
Revises: f32db964a2a0
Create Date: 2026-09-19 16:33:57.523000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "198c8c108788"
down_revision: str | Sequence[str] | None = "f32db964a2a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- InventoryReservation: add order_item_id ---
    op.add_column(
        "inventory_reservations",
        sa.Column("order_item_id", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        op.f("ix_inventory_reservations_order_item_id"),
        "inventory_reservations",
        ["order_item_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_inventory_reservations_order_item",
        "inventory_reservations",
        "order_items",
        ["order_item_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # --- OrderItem: unique constraint per tenant/order/product ---
    op.create_unique_constraint(
        "uq_order_items_tenant_order_product",
        "order_items",
        ["tenant_id", "order_id", "product_id"],
    )

    # --- Order: convert order_number from VARCHAR(50) to BIGINT ---
    # Data is safe to convert: verified no non-numeric values exist.
    op.execute(
        "ALTER TABLE orders ALTER COLUMN order_number TYPE BIGINT "
        "USING order_number::bigint"
    )

    # --- Order: customer_id NOT NULL ---
    op.alter_column("orders", "customer_id", nullable=False)

    # --- Order: status default DRAFT ---
    op.alter_column(
        "orders",
        "status",
        server_default="DRAFT",
    )


def downgrade() -> None:
    # --- Order: revert status default ---
    op.alter_column(
        "orders",
        "status",
        server_default=sa.text("'pending'::character varying"),
    )

    # --- Order: customer_id nullable ---
    op.alter_column("orders", "customer_id", nullable=True)

    # --- Order: convert order_number back to VARCHAR(50) ---
    op.execute(
        "ALTER TABLE orders ALTER COLUMN order_number TYPE VARCHAR(50) "
        "USING order_number::text"
    )

    # --- OrderItem: drop unique constraint ---
    op.drop_constraint(
        "uq_order_items_tenant_order_product", "order_items", type_="unique"
    )

    # --- InventoryReservation: drop FK, index, column ---
    op.drop_constraint(
        "fk_inventory_reservations_order_item",
        "inventory_reservations",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_inventory_reservations_order_item_id"),
        table_name="inventory_reservations",
    )
    op.drop_column("inventory_reservations", "order_item_id")
