from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.db.models.categoria import Categoria
from app.db.models.inventory import Inventory
from app.db.models.inventory_movement import InventoryMovement, MovementType
from app.db.models.inventory_reservation import InventoryReservation, ReservationStatus
from app.db.models.permission import Permission
from app.db.models.produto import Produto
from app.db.models.role import Role
from app.db.models.role_permission import RolePermission
from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.db.models.user_role import UserRole


async def _create_permission(
    session: AsyncSession,
    tenant_id: int,
    name: str,
) -> Permission:
    stmt = select(Permission).where(
        Permission.tenant_id == tenant_id,
        Permission.name == name,
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    perm = Permission(tenant_id=tenant_id, name=name)
    session.add(perm)
    await session.flush()
    return perm


async def _create_role_with_perms(
    session: AsyncSession,
    tenant_id: int,
    name: str,
    perm_names: list[str],
) -> Role:
    stmt = select(Role).where(
        Role.tenant_id == tenant_id,
        Role.name == name,
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    role = Role(tenant_id=tenant_id, name=name)
    session.add(role)
    await session.flush()
    for pname in perm_names:
        perm = await _create_permission(session, tenant_id, pname)
        stmt_rp = select(RolePermission).where(
            RolePermission.tenant_id == tenant_id,
            RolePermission.role_id == role.id,
            RolePermission.permission_id == perm.id,
        )
        rp_result = await session.execute(stmt_rp)
        if rp_result.scalar_one_or_none() is None:
            rp = RolePermission(
                tenant_id=tenant_id,
                role_id=role.id,
                permission_id=perm.id,
            )
            session.add(rp)
            await session.flush()
    return role


async def _assign_role_to_user(
    session: AsyncSession,
    tenant_id: int,
    user_id: int,
    role_id: int,
) -> None:
    stmt = select(UserRole).where(
        UserRole.tenant_id == tenant_id,
        UserRole.user_id == user_id,
        UserRole.role_id == role_id,
    )
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        return
    ur = UserRole(
        tenant_id=tenant_id,
        user_id=user_id,
        role_id=role_id,
    )
    session.add(ur)
    await session.flush()


async def _create_categoria_in_db(
    session: AsyncSession,
    tenant_id: int,
    name: str,
) -> Categoria:
    categoria = Categoria(
        tenant_id=tenant_id,
        name=name,
    )
    session.add(categoria)
    await session.flush()
    return categoria


async def _create_produto_in_db(
    session: AsyncSession,
    tenant_id: int,
    name: str,
    sku: str,
    categoria_id: int | None = None,
    price: Decimal = Decimal("10.00"),
    is_active: bool = True,
) -> Produto:
    produto = Produto(
        tenant_id=tenant_id,
        sku=sku,
        name=name,
        categoria_id=categoria_id,
        price=price,
        is_active=is_active,
    )
    session.add(produto)
    await session.flush()
    return produto


async def _create_inventory_in_db(
    session: AsyncSession,
    tenant_id: int,
    produto_id: int,
    quantity: Decimal = Decimal("100.000"),
    reserved_quantity: Decimal = Decimal("0.000"),
) -> Inventory:
    inventory = Inventory(
        tenant_id=tenant_id,
        produto_id=produto_id,
        quantity=quantity,
        reserved_quantity=reserved_quantity,
    )
    session.add(inventory)
    await session.flush()
    return inventory


async def _create_movement_in_db(
    session: AsyncSession,
    tenant_id: int,
    produto_id: int,
    movement_type: str = "IN",
    quantity: Decimal = Decimal("10.000"),
    idempotency_key: str = "test-key",
) -> InventoryMovement:
    movement = InventoryMovement(
        tenant_id=tenant_id,
        produto_id=produto_id,
        movement_type=MovementType(movement_type),
        quantity=quantity,
        idempotency_key=idempotency_key,
    )
    session.add(movement)
    await session.flush()
    return movement


async def _create_reservation_in_db(
    session: AsyncSession,
    tenant_id: int,
    produto_id: int,
    quantity: Decimal = Decimal("5.000"),
    status: ReservationStatus = ReservationStatus.ACTIVE,
    idempotency_key: str = "test-reservation-key",
) -> InventoryReservation:
    reservation = InventoryReservation(
        tenant_id=tenant_id,
        produto_id=produto_id,
        quantity=quantity,
        status=status,
        idempotency_key=idempotency_key,
    )
    session.add(reservation)
    await session.flush()
    return reservation


@pytest.fixture
async def all_inventory_perms(
    db_session: AsyncSession,
    test_tenant: Tenant,
) -> Role:
    return await _create_role_with_perms(
        db_session,
        test_tenant.id,
        "inventory_admin",
        [
            "inventory.read",
            "inventory.update",
        ],
    )


@pytest.fixture
async def read_only_inventory_perms(
    db_session: AsyncSession,
    test_tenant: Tenant,
) -> Role:
    return await _create_role_with_perms(
        db_session,
        test_tenant.id,
        "inventory_reader",
        [
            "inventory.read",
        ],
    )


@pytest.fixture
async def admin_user(
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    all_inventory_perms: Role,
) -> User:
    await _assign_role_to_user(
        db_session, test_tenant.id, test_user.id, all_inventory_perms.id
    )
    await db_session.commit()
    return test_user


@pytest.fixture
async def admin_headers(
    admin_user: User,
    test_tenant: Tenant,
) -> dict[str, str]:
    token = create_access_token(
        data={
            "sub": str(admin_user.id),
            "tenant_id": str(test_tenant.id),
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def read_only_user(
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    read_only_inventory_perms: Role,
) -> User:
    await _assign_role_to_user(
        db_session, test_tenant.id, test_user.id, read_only_inventory_perms.id
    )
    await db_session.commit()
    return test_user


@pytest.fixture
async def read_only_headers(
    read_only_user: User,
    test_tenant: Tenant,
) -> dict[str, str]:
    token = create_access_token(
        data={
            "sub": str(read_only_user.id),
            "tenant_id": str(test_tenant.id),
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def other_tenant(db_session: AsyncSession) -> Tenant:
    tenant = Tenant(
        name="Other Tenant",
        slug="other-inventory-tenant",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant


@pytest.fixture
async def other_tenant_user(
    db_session: AsyncSession,
    other_tenant: Tenant,
) -> User:
    user = User(
        tenant_id=other_tenant.id,
        email="other@example.com",
        full_name="Other User",
        is_active=True,
        password_hash=get_password_hash("password123"),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def other_tenant_headers(
    db_session: AsyncSession,
    other_tenant_user: User,
    other_tenant: Tenant,
) -> dict[str, str]:
    role = await _create_role_with_perms(
        db_session,
        other_tenant.id,
        "other_inventory_all",
        [
            "inventory.read",
            "inventory.update",
        ],
    )
    await _assign_role_to_user(
        db_session, other_tenant.id, other_tenant_user.id, role.id
    )
    await db_session.commit()
    token = create_access_token(
        data={
            "sub": str(other_tenant_user.id),
            "tenant_id": str(other_tenant.id),
        }
    )
    return {"Authorization": f"Bearer {token}"}


# --- Movement tests ---


@pytest.mark.asyncio
async def test_create_in_movement(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto A", "SKU-A", categoria.id
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/movements",
        json={
            "produto_id": produto.id,
            "movement_type": "IN",
            "quantity": "50.000",
            "reference": "PO-001",
            "idempotency_key": "in-movement-1",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["movement_type"] == "IN"
    assert data["quantity"] == "50.000"
    assert data["produto_id"] == produto.id
    assert data["reference"] == "PO-001"


@pytest.mark.asyncio
async def test_create_out_movement(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto B", "SKU-B", categoria.id
    )
    await _create_inventory_in_db(db_session, test_tenant.id, produto.id)
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/movements",
        json={
            "produto_id": produto.id,
            "movement_type": "OUT",
            "quantity": "10.000",
            "idempotency_key": "out-movement-1",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["movement_type"] == "OUT"
    assert data["quantity"] == "10.000"


@pytest.mark.asyncio
async def test_adjustment_movement(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto C", "SKU-C", categoria.id
    )
    await _create_inventory_in_db(db_session, test_tenant.id, produto.id)
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/movements",
        json={
            "produto_id": produto.id,
            "movement_type": "ADJUSTMENT",
            "quantity": "75.000",
            "notes": "Stock count correction",
            "idempotency_key": "adj-movement-1",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["movement_type"] == "ADJUSTMENT"


@pytest.mark.asyncio
async def test_movement_updates_balance(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto D", "SKU-D", categoria.id
    )
    await _create_inventory_in_db(
        db_session, test_tenant.id, produto.id, quantity=Decimal("50.000")
    )
    await db_session.commit()

    await client.post(
        "/api/v1/inventory/movements",
        json={
            "produto_id": produto.id,
            "movement_type": "IN",
            "quantity": "25.000",
            "idempotency_key": "in-25",
        },
        headers=admin_headers,
    )

    response = await client.get(
        f"/api/v1/inventory/{produto.id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == "75.000"


@pytest.mark.asyncio
async def test_out_movement_insufficient_stock(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto E", "SKU-E", categoria.id
    )
    await _create_inventory_in_db(
        db_session, test_tenant.id, produto.id, quantity=Decimal("5.000")
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/movements",
        json={
            "produto_id": produto.id,
            "movement_type": "OUT",
            "quantity": "10.000",
            "idempotency_key": "out-10",
        },
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_out_movement_cannot_consume_reserved(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto F", "SKU-F", categoria.id
    )
    await _create_inventory_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        quantity=Decimal("10.000"),
        reserved_quantity=Decimal("5.000"),
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/movements",
        json={
            "produto_id": produto.id,
            "movement_type": "OUT",
            "quantity": "8.000",
            "idempotency_key": "out-8",
        },
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_adjustment_leaves_reserved_exceeds_quantity(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto G", "SKU-G", categoria.id
    )
    await _create_inventory_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        quantity=Decimal("10.000"),
        reserved_quantity=Decimal("5.000"),
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/movements",
        json={
            "produto_id": produto.id,
            "movement_type": "ADJUSTMENT",
            "quantity": "3.000",
            "idempotency_key": "adj-3",
        },
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_idempotent_movement_returns_same(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto H", "SKU-H", categoria.id
    )
    await db_session.commit()

    response1 = await client.post(
        "/api/v1/inventory/movements",
        json={
            "produto_id": produto.id,
            "movement_type": "IN",
            "quantity": "10.000",
            "idempotency_key": "idempotent-1",
        },
        headers=admin_headers,
    )
    assert response1.status_code == 201

    response2 = await client.post(
        "/api/v1/inventory/movements",
        json={
            "produto_id": produto.id,
            "movement_type": "IN",
            "quantity": "20.000",
            "idempotency_key": "idempotent-1",
        },
        headers=admin_headers,
    )
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_list_movements(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto I", "SKU-I", categoria.id
    )
    await _create_movement_in_db(
        db_session, test_tenant.id, produto.id, "IN", Decimal("10.000"), "key-1"
    )
    await _create_movement_in_db(
        db_session, test_tenant.id, produto.id, "OUT", Decimal("5.000"), "key-2"
    )
    await db_session.commit()

    response = await client.get(
        "/api/v1/inventory/movements/list",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


# --- Reservation tests ---


@pytest.mark.asyncio
async def test_create_reservation(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto J", "SKU-J", categoria.id
    )
    await _create_inventory_in_db(db_session, test_tenant.id, produto.id)
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/reservations",
        json={
            "produto_id": produto.id,
            "quantity": "5.000",
            "reference": "SO-001",
            "idempotency_key": "res-1",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ACTIVE"
    assert data["quantity"] == "5.000"
    assert data["produto_id"] == produto.id


@pytest.mark.asyncio
async def test_reservation_updates_reserved_quantity(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto K", "SKU-K", categoria.id
    )
    await _create_inventory_in_db(
        db_session, test_tenant.id, produto.id, quantity=Decimal("20.000")
    )
    await db_session.commit()

    await client.post(
        "/api/v1/inventory/reservations",
        json={
            "produto_id": produto.id,
            "quantity": "7.000",
            "idempotency_key": "res-7",
        },
        headers=admin_headers,
    )

    response = await client.get(
        f"/api/v1/inventory/{produto.id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["reserved_quantity"] == "7.000"
    assert data["quantity"] == "20.000"


@pytest.mark.asyncio
async def test_reservation_insufficient_stock(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto L", "SKU-L", categoria.id
    )
    await _create_inventory_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        quantity=Decimal("10.000"),
        reserved_quantity=Decimal("8.000"),
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/reservations",
        json={
            "produto_id": produto.id,
            "quantity": "5.000",
            "idempotency_key": "res-over",
        },
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_reservation_inactive_produto(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto M", "SKU-M", categoria.id, is_active=False
    )
    await _create_inventory_in_db(db_session, test_tenant.id, produto.id)
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/reservations",
        json={
            "produto_id": produto.id,
            "quantity": "2.000",
            "idempotency_key": "res-inactive",
        },
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_confirm_reservation(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto N", "SKU-N", categoria.id
    )
    inventory = await _create_inventory_in_db(
        db_session, test_tenant.id, produto.id, quantity=Decimal("20.000")
    )
    reservation = await _create_reservation_in_db(
        db_session, test_tenant.id, produto.id, Decimal("5.000")
    )
    inventory.reserved_quantity = Decimal("5.000")
    await db_session.commit()

    response = await client.post(
        f"/api/v1/inventory/reservations/{reservation.id}/confirm",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CONFIRMED"
    assert data["confirmed_at"] is not None

    response2 = await client.get(
        f"/api/v1/inventory/{produto.id}",
        headers=admin_headers,
    )
    assert response2.json()["reserved_quantity"] == "0.000"


@pytest.mark.asyncio
async def test_release_reservation(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto O", "SKU-O", categoria.id
    )
    inventory = await _create_inventory_in_db(
        db_session, test_tenant.id, produto.id, quantity=Decimal("20.000")
    )
    reservation = await _create_reservation_in_db(
        db_session, test_tenant.id, produto.id, Decimal("5.000")
    )
    inventory.reserved_quantity = Decimal("5.000")
    await db_session.commit()

    response = await client.post(
        f"/api/v1/inventory/reservations/{reservation.id}/release",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RELEASED"
    assert data["released_at"] is not None


@pytest.mark.asyncio
async def test_cancel_reservation(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto P", "SKU-P", categoria.id
    )
    inventory = await _create_inventory_in_db(
        db_session, test_tenant.id, produto.id, quantity=Decimal("20.000")
    )
    reservation = await _create_reservation_in_db(
        db_session, test_tenant.id, produto.id, Decimal("5.000")
    )
    inventory.reserved_quantity = Decimal("5.000")
    await db_session.commit()

    response = await client.post(
        f"/api/v1/inventory/reservations/{reservation.id}/cancel",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CANCELLED"
    assert data["released_at"] is not None


@pytest.mark.asyncio
async def test_confirm_already_confirmed_reservation(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto Q", "SKU-Q", categoria.id
    )
    reservation = await _create_reservation_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        Decimal("5.000"),
        ReservationStatus.CONFIRMED,
    )
    await db_session.commit()

    response = await client.post(
        f"/api/v1/inventory/reservations/{reservation.id}/confirm",
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_reservations(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto R", "SKU-R", categoria.id
    )
    await _create_reservation_in_db(
        db_session, test_tenant.id, produto.id, Decimal("5.000"), idempotency_key="r1"
    )
    await _create_reservation_in_db(
        db_session, test_tenant.id, produto.id, Decimal("3.000"), idempotency_key="r2"
    )
    await db_session.commit()

    response = await client.get(
        "/api/v1/inventory/reservations/list",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


# --- Balance tests ---


@pytest.mark.asyncio
async def test_list_inventory_balances(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    p1 = await _create_produto_in_db(
        db_session, test_tenant.id, "Prod 1", "SKU-1", categoria.id
    )
    p2 = await _create_produto_in_db(
        db_session, test_tenant.id, "Prod 2", "SKU-2", categoria.id
    )
    await _create_inventory_in_db(db_session, test_tenant.id, p1.id)
    await _create_inventory_in_db(db_session, test_tenant.id, p2.id)
    await db_session.commit()

    response = await client.get(
        "/api/v1/inventory",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_get_single_balance(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Prod Single", "SKU-S", categoria.id
    )
    await _create_inventory_in_db(
        db_session, test_tenant.id, produto.id, quantity=Decimal("42.000")
    )
    await db_session.commit()

    response = await client.get(
        f"/api/v1/inventory/{produto.id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == "42.000"
    assert data["produto_id"] == produto.id


@pytest.mark.asyncio
async def test_get_nonexistent_balance(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    response = await client.get(
        "/api/v1/inventory/99999",
        headers=admin_headers,
    )
    assert response.status_code == 404


# --- Multi-tenancy tests ---


@pytest.mark.asyncio
async def test_cannot_access_other_tenant_inventory(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    other_tenant: Tenant,
    other_tenant_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "TenantProd", "SKU-TP", categoria.id
    )
    await _create_inventory_in_db(db_session, test_tenant.id, produto.id)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/inventory/{produto.id}",
        headers=other_tenant_headers,
    )
    assert response.status_code == 404


# --- RBAC tests ---


@pytest.mark.asyncio
async def test_read_only_user_can_list(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    read_only_headers: dict[str, str],
) -> None:
    response = await client.get(
        "/api/v1/inventory",
        headers=read_only_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_read_only_user_cannot_create_movement(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
) -> None:
    ro_role = await _create_role_with_perms(
        db_session, test_tenant.id, "inv_readonly", ["inventory.read"]
    )
    ro_user = User(
        tenant_id=test_tenant.id,
        email="readonly@example.com",
        full_name="Read Only",
        is_active=True,
        password_hash=get_password_hash("pass123"),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(ro_user)
    await db_session.flush()
    await _assign_role_to_user(db_session, test_tenant.id, ro_user.id, ro_role.id)
    await db_session.commit()

    ro_token = create_access_token(
        data={"sub": str(ro_user.id), "tenant_id": str(test_tenant.id)}
    )
    ro_headers = {"Authorization": f"Bearer {ro_token}"}

    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "ProdRO", "SKU-RO", categoria.id
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/movements",
        json={
            "produto_id": produto.id,
            "movement_type": "IN",
            "quantity": "10.000",
            "idempotency_key": "ro-movement",
        },
        headers=ro_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_cannot_access(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/inventory")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_movement_on_inactive_produto_allowed(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session,
        test_tenant.id,
        "Inactive",
        "SKU-INACT",
        categoria.id,
        is_active=False,
    )
    await _create_inventory_in_db(db_session, test_tenant.id, produto.id)
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/movements",
        json={
            "produto_id": produto.id,
            "movement_type": "IN",
            "quantity": "5.000",
            "idempotency_key": "inactive-in",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_adjustment_must_be_positive(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "AdjProd", "SKU-ADJ", categoria.id
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/movements",
        json={
            "produto_id": produto.id,
            "movement_type": "ADJUSTMENT",
            "quantity": "0.000",
            "idempotency_key": "adj-zero",
        },
        headers=admin_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_movement_type(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "BadType", "SKU-BT", categoria.id
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/movements",
        json={
            "produto_id": produto.id,
            "movement_type": "INVALID",
            "quantity": "5.000",
            "idempotency_key": "bad-type",
        },
        headers=admin_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_pagination_works(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "PagProd", "SKU-PAG", categoria.id
    )
    for i in range(5):
        await _create_movement_in_db(
            db_session,
            test_tenant.id,
            produto.id,
            "IN",
            Decimal("1.000"),
            f"pag-key-{i}",
        )
    await db_session.commit()

    response = await client.get(
        "/api/v1/inventory/movements/list?page=1&page_size=2",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2


# --- Critical audit tests ---


@pytest.mark.asyncio
async def test_idempotent_reservation_returns_same(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "IdemRes", "SKU-IR", categoria.id
    )
    await _create_inventory_in_db(
        db_session, test_tenant.id, produto.id, quantity=Decimal("50.000")
    )
    await db_session.commit()

    response1 = await client.post(
        "/api/v1/inventory/reservations",
        json={
            "produto_id": produto.id,
            "quantity": "10.000",
            "idempotency_key": "res-idempotent-1",
        },
        headers=admin_headers,
    )
    assert response1.status_code == 201
    assert response1.json()["status"] == "ACTIVE"

    response2 = await client.post(
        "/api/v1/inventory/reservations",
        json={
            "produto_id": produto.id,
            "quantity": "20.000",
            "idempotency_key": "res-idempotent-1",
        },
        headers=admin_headers,
    )
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_released_reservation_cannot_be_confirmed(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "RelCf", "SKU-RC", categoria.id
    )
    reservation = await _create_reservation_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        Decimal("5.000"),
        ReservationStatus.RELEASED,
    )
    await db_session.commit()

    response = await client.post(
        f"/api/v1/inventory/reservations/{reservation.id}/confirm",
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_cancelled_reservation_cannot_be_confirmed(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "CanCf", "SKU-CC", categoria.id
    )
    reservation = await _create_reservation_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        Decimal("5.000"),
        ReservationStatus.CANCELLED,
    )
    await db_session.commit()

    response = await client.post(
        f"/api/v1/inventory/reservations/{reservation.id}/confirm",
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_confirmed_reservation_cannot_be_released(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "CfRel", "SKU-CR", categoria.id
    )
    reservation = await _create_reservation_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        Decimal("5.000"),
        ReservationStatus.CONFIRMED,
    )
    await db_session.commit()

    response = await client.post(
        f"/api/v1/inventory/reservations/{reservation.id}/release",
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_out_at_boundary_exactly_available(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "BoundOut", "SKU-BO", categoria.id
    )
    await _create_inventory_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        quantity=Decimal("100.000"),
        reserved_quantity=Decimal("30.000"),
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/movements",
        json={
            "produto_id": produto.id,
            "movement_type": "OUT",
            "quantity": "70.000",
            "idempotency_key": "out-boundary-ok",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_out_one_over_boundary_fails(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "BoundOutFail", "SKU-BOF", categoria.id
    )
    await _create_inventory_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        quantity=Decimal("100.000"),
        reserved_quantity=Decimal("30.000"),
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/movements",
        json={
            "produto_id": produto.id,
            "movement_type": "OUT",
            "quantity": "71.000",
            "idempotency_key": "out-boundary-fail",
        },
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_cross_tenant_cannot_create_movement_on_other_tenant_produto(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    other_tenant: Tenant,
    other_tenant_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "CrossTenant", "SKU-CT", categoria.id
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/movements",
        json={
            "produto_id": produto.id,
            "movement_type": "IN",
            "quantity": "10.000",
            "idempotency_key": "cross-tenant-movement",
        },
        headers=other_tenant_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cross_tenant_cannot_create_reservation_on_other_tenant_produto(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    other_tenant: Tenant,
    other_tenant_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "CrossTenantRes", "SKU-CTR", categoria.id
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/inventory/reservations",
        json={
            "produto_id": produto.id,
            "quantity": "5.000",
            "idempotency_key": "cross-tenant-reservation",
        },
        headers=other_tenant_headers,
    )
    assert response.status_code == 404
