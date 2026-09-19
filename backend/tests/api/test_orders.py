from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.customer import Customer
from app.db.models.inventory import Inventory
from app.db.models.order import Order
from app.db.models.permission import Permission
from app.db.models.product import Product
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


async def _create_customer_in_db(
    session: AsyncSession,
    tenant_id: int,
    name: str,
) -> Customer:
    customer = Customer(
        tenant_id=tenant_id,
        name=name,
    )
    session.add(customer)
    await session.flush()
    return customer


async def _create_product_in_db(
    session: AsyncClient,
    tenant_id: int,
    name: str,
    price: Decimal = Decimal("10.00"),
    is_active: bool = True,
) -> Product:
    product = Product(
        tenant_id=tenant_id,
        sku=f"SKU-{name.upper().replace(' ', '-')}",
        name=name,
        price=price,
        is_active=is_active,
    )
    session = product  # type: ignore[assignment]
    session = None  # noqa: F841  # will be passed as parameter
    return product


async def _create_product(
    session: AsyncSession,
    tenant_id: int,
    name: str,
    price: Decimal = Decimal("10.00"),
    is_active: bool = True,
) -> Product:
    product = Product(
        tenant_id=tenant_id,
        sku=f"SKU-{name.upper().replace(' ', '-')}",
        name=name,
        price=price,
        is_active=is_active,
    )
    session.add(product)
    await session.flush()
    return product


async def _create_inventory(
    session: AsyncSession,
    tenant_id: int,
    product_id: int,
    quantity: Decimal = Decimal("100.000"),
) -> Inventory:
    inventory = Inventory(
        tenant_id=tenant_id,
        product_id=product_id,
        quantity=quantity,
    )
    session.add(inventory)
    await session.flush()
    return inventory


@pytest.fixture
async def customer(db_session: AsyncSession, test_tenant: Tenant) -> Customer:
    return await _create_customer_in_db(db_session, test_tenant.id, "Cliente Teste")


@pytest.fixture
async def product(db_session: AsyncSession, test_tenant: Tenant) -> Product:
    return await _create_product(db_session, test_tenant.id, "Produto Teste")


@pytest.fixture
async def product_b(db_session: AsyncSession, test_tenant: Tenant) -> Product:
    return await _create_product(
        db_session, test_tenant.id, "Produto B", price=Decimal("25.00")
    )


@pytest.fixture
async def inventory(
    db_session: AsyncSession, test_tenant: Tenant, product: Product
) -> Inventory:
    return await _create_inventory(db_session, test_tenant.id, product.id)


@pytest.fixture
async def inventory_b(
    db_session: AsyncSession, test_tenant: Tenant, product_b: Product
) -> Inventory:
    return await _create_inventory(db_session, test_tenant.id, product_b.id)


@pytest.fixture
async def order_with_items(
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    customer: Customer,
    product: Product,
    inventory: Inventory,
) -> Order:
    role = await _create_role_with_perms(
        db_session,
        test_tenant.id,
        "order_admin",
        [
            "order.read",
            "order.create",
            "order.update",
            "order.cancel",
        ],
    )
    await _assign_role_to_user(db_session, test_tenant.id, test_user.id, role.id)
    await db_session.commit()
    return customer  # type: ignore[return-value]


class TestOrderCreate:
    async def test_create_order_with_items(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_creator",
            ["order.read", "order.create"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        response = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 2}],
            },
            headers=authenticated_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "DRAFT"
        assert data["customer_id"] == customer.id
        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == product.id
        assert data["items"][0]["quantity"] == 2.0
        assert data["items"][0]["unit_price"] == float(product.price)
        assert data["total_amount"] == float(product.price) * 2
        assert isinstance(data["order_number"], int)

    async def test_create_order_multiple_items(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        product_b: Product,
        inventory: Inventory,
        inventory_b: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_creator",
            ["order.read", "order.create"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        response = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [
                    {"product_id": product.id, "quantity": 2},
                    {"product_id": product_b.id, "quantity": 1},
                ],
            },
            headers=authenticated_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["items"]) == 2
        expected_total = float(product.price) * 2 + float(product_b.price) * 1
        assert float(Decimal(str(data["total_amount"]))) == expected_total

    async def test_create_order_empty_items_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_creator",
            ["order.read", "order.create"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        response = await client.post(
            "/api/v1/orders",
            json={"customer_id": customer.id, "items": []},
            headers=authenticated_headers,
        )
        assert response.status_code == 422

    async def test_create_order_nonexistent_customer_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_creator",
            ["order.read", "order.create"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        response = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": 99999,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        assert response.status_code == 409

    async def test_create_order_nonexistent_product_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_creator",
            ["order.read", "order.create"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        response = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": 99999, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        assert response.status_code == 409

    async def test_create_order_duplicate_product_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_creator",
            ["order.read", "order.create"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        response = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [
                    {"product_id": product.id, "quantity": 1},
                    {"product_id": product.id, "quantity": 2},
                ],
            },
            headers=authenticated_headers,
        )
        assert response.status_code == 409

    async def test_create_order_with_custom_unit_price(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_creator",
            ["order.read", "order.create"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        custom_price = Decimal("99.99")
        response = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [
                    {
                        "product_id": product.id,
                        "quantity": 3,
                        "unit_price": str(custom_price),
                    }
                ],
            },
            headers=authenticated_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["items"][0]["unit_price"] == float(custom_price)
        assert abs(Decimal(str(data["total_amount"])) - custom_price * 3) < Decimal(
            "0.01"
        )


class TestOrderNumber:
    async def test_order_number_sequential(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_creator",
            ["order.read", "order.create"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        resp1 = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        assert resp1.status_code == 201
        num1 = resp1.json()["order_number"]

        resp2 = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        assert resp2.status_code == 201
        num2 = resp2.json()["order_number"]

        assert num2 == num1 + 1


class TestOrderListAndDetail:
    async def test_list_orders(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_list",
            ["order.read", "order.create"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )

        response = await client.get(
            "/api/v1/orders",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    async def test_list_orders_filter_by_status(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_list",
            ["order.read", "order.create"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )

        response = await client.get(
            "/api/v1/orders",
            params={"status": "DRAFT"},
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        for item in response.json()["items"]:
            assert item["status"] == "DRAFT"

    async def test_get_order_detail(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_detail",
            ["order.read", "order.create"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]

        response = await client.get(
            f"/api/v1/orders/{order_id}",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert len(data["items"]) == 1

    async def test_get_nonexistent_order_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_detail",
            ["order.read"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        response = await client.get(
            "/api/v1/orders/99999",
            headers=authenticated_headers,
        )
        assert response.status_code == 404


class TestOrderUpdate:
    async def test_update_order_customer(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_update",
            ["order.read", "order.create", "order.update"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]

        new_customer = await _create_customer_in_db(
            db_session, test_tenant.id, "Novo Cliente"
        )
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/orders/{order_id}",
            json={"customer_id": new_customer.id},
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert response.json()["customer_id"] == new_customer.id

    async def test_update_order_not_draft_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_update",
            ["order.read", "order.create", "order.update", "order.cancel"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/orders/{order_id}/confirm",
            headers=authenticated_headers,
        )

        response = await client.patch(
            f"/api/v1/orders/{order_id}",
            json={"notes": "Should fail"},
            headers=authenticated_headers,
        )
        assert response.status_code == 409


class TestOrderItems:
    async def test_add_item_to_order(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        product_b: Product,
        inventory: Inventory,
        inventory_b: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_items",
            ["order.read", "order.create", "order.update"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/orders/{order_id}/items",
            json={"product_id": product_b.id, "quantity": 3},
            headers=authenticated_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["product_id"] == product_b.id
        assert data["quantity"] == 3.0

        detail_resp = await client.get(
            f"/api/v1/orders/{order_id}",
            headers=authenticated_headers,
        )
        assert detail_resp.status_code == 200
        assert len(detail_resp.json()["items"]) == 2

    async def test_add_duplicate_product_to_order_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_items",
            ["order.read", "order.create", "order.update"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/orders/{order_id}/items",
            json={"product_id": product.id, "quantity": 2},
            headers=authenticated_headers,
        )
        assert response.status_code == 409

    async def test_update_item_quantity(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_items",
            ["order.read", "order.create", "order.update"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]
        item_id = create_resp.json()["items"][0]["id"]

        response = await client.patch(
            f"/api/v1/orders/{order_id}/items/{item_id}",
            json={"quantity": 5},
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert response.json()["quantity"] == 5.0

        detail_resp = await client.get(
            f"/api/v1/orders/{order_id}",
            headers=authenticated_headers,
        )
        assert (
            float(Decimal(str(detail_resp.json()["total_amount"])))
            == float(product.price) * 5
        )

    async def test_remove_item_from_order(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        product_b: Product,
        inventory: Inventory,
        inventory_b: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_items",
            ["order.read", "order.create", "order.update"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [
                    {"product_id": product.id, "quantity": 1},
                    {"product_id": product_b.id, "quantity": 2},
                ],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]
        item_to_remove = create_resp.json()["items"][1]["id"]

        response = await client.delete(
            f"/api/v1/orders/{order_id}/items/{item_to_remove}",
            headers=authenticated_headers,
        )
        assert response.status_code == 204

        detail_resp = await client.get(
            f"/api/v1/orders/{order_id}",
            headers=authenticated_headers,
        )
        assert len(detail_resp.json()["items"]) == 1

    async def test_remove_last_item_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_items",
            ["order.read", "order.create", "order.update"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]
        item_id = create_resp.json()["items"][0]["id"]

        response = await client.delete(
            f"/api/v1/orders/{order_id}/items/{item_id}",
            headers=authenticated_headers,
        )
        assert response.status_code == 409

    async def test_add_item_to_non_draft_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        product_b: Product,
        inventory: Inventory,
        inventory_b: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_items",
            ["order.read", "order.create", "order.update", "order.cancel"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/orders/{order_id}/confirm",
            headers=authenticated_headers,
        )

        response = await client.post(
            f"/api/v1/orders/{order_id}/items",
            json={"product_id": product_b.id, "quantity": 1},
            headers=authenticated_headers,
        )
        assert response.status_code == 409


class TestOrderStateMachine:
    async def test_confirm_order(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_confirm",
            [
                "order.read",
                "order.create",
                "order.update",
                "inventory.read",
                "inventory.update",
            ],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 5}],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/orders/{order_id}/confirm",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "CONFIRMED"

        inv_resp = await client.get(
            f"/api/v1/inventory/{product.id}",
            headers=authenticated_headers,
        )
        assert inv_resp.status_code == 200
        assert float(inv_resp.json()["reserved_quantity"]) == 5.0

    async def test_complete_order(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_complete",
            ["order.read", "order.create", "order.update", "inventory.read"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 5}],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/orders/{order_id}/confirm",
            headers=authenticated_headers,
        )

        response = await client.post(
            f"/api/v1/orders/{order_id}/complete",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "COMPLETED"

        inv_resp = await client.get(
            f"/api/v1/inventory/{product.id}",
            headers=authenticated_headers,
        )
        assert inv_resp.status_code == 200
        assert float(inv_resp.json()["quantity"]) == 95.0
        assert float(inv_resp.json()["reserved_quantity"]) == 0.0

    async def test_cancel_draft_order(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_cancel",
            ["order.read", "order.create", "order.update", "order.cancel"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 5}],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/orders/{order_id}/cancel",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "CANCELLED"

    async def test_cancel_confirmed_order_releases_reservations(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_cancel",
            [
                "order.read",
                "order.create",
                "order.update",
                "order.cancel",
                "inventory.read",
            ],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 5}],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/orders/{order_id}/confirm",
            headers=authenticated_headers,
        )

        response = await client.post(
            f"/api/v1/orders/{order_id}/cancel",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "CANCELLED"

        inv_resp = await client.get(
            f"/api/v1/inventory/{product.id}",
            headers=authenticated_headers,
        )
        assert inv_resp.status_code == 200
        assert float(inv_resp.json()["reserved_quantity"]) == 0.0

    async def test_complete_without_confirm_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_complete",
            ["order.read", "order.create", "order.update"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/orders/{order_id}/complete",
            headers=authenticated_headers,
        )
        assert response.status_code == 409

    async def test_confirm_completed_order_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_terminal",
            ["order.read", "order.create", "order.update"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/orders/{order_id}/confirm",
            headers=authenticated_headers,
        )
        await client.post(
            f"/api/v1/orders/{order_id}/complete",
            headers=authenticated_headers,
        )

        response = await client.post(
            f"/api/v1/orders/{order_id}/confirm",
            headers=authenticated_headers,
        )
        assert response.status_code == 409

    async def test_confirm_cancelled_order_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_terminal",
            ["order.read", "order.create", "order.update", "order.cancel"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/orders/{order_id}/cancel",
            headers=authenticated_headers,
        )

        response = await client.post(
            f"/api/v1/orders/{order_id}/confirm",
            headers=authenticated_headers,
        )
        assert response.status_code == 409


class TestOrderRBAC:
    async def test_create_order_no_permission_fails(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        authenticated_headers: dict,
    ) -> None:
        response = await client.post(
            "/api/v1/orders",
            json={"customer_id": 1, "items": [{"product_id": 1, "quantity": 1}]},
            headers=authenticated_headers,
        )
        assert response.status_code == 403

    async def test_list_orders_no_permission_fails(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        authenticated_headers: dict,
    ) -> None:
        response = await client.get(
            "/api/v1/orders",
            headers=authenticated_headers,
        )
        assert response.status_code == 403

    async def test_get_order_no_permission_fails(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        authenticated_headers: dict,
    ) -> None:
        response = await client.get(
            "/api/v1/orders/1",
            headers=authenticated_headers,
        )
        assert response.status_code == 403


class TestOrderMultiTenancy:
    async def test_cannot_access_other_tenant_order(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        from app.core.security import create_access_token

        other_tenant = Tenant(name="Outro Tenant", slug="outro-tenant")
        db_session.add(other_tenant)
        await db_session.flush()

        other_customer = Customer(tenant_id=other_tenant.id, name="Outro Cliente")
        db_session.add(other_customer)
        await db_session.flush()

        other_product = Product(
            tenant_id=other_tenant.id,
            sku="SKU-OUTRO",
            name="Outro Produto",
            price=Decimal("50.00"),
        )
        db_session.add(other_product)
        await db_session.flush()

        other_inventory = Inventory(
            tenant_id=other_tenant.id,
            product_id=other_product.id,
            quantity=Decimal("100.000"),
        )
        db_session.add(other_inventory)
        await db_session.flush()

        other_perm = Permission(tenant_id=other_tenant.id, name="order.read")
        db_session.add(other_perm)
        await db_session.flush()

        other_perm_create = Permission(tenant_id=other_tenant.id, name="order.create")
        db_session.add(other_perm_create)
        await db_session.flush()

        other_role = Role(tenant_id=other_tenant.id, name="admin")
        db_session.add(other_role)
        await db_session.flush()

        other_rp1 = RolePermission(
            tenant_id=other_tenant.id,
            role_id=other_role.id,
            permission_id=other_perm.id,
        )
        db_session.add(other_rp1)

        other_rp2 = RolePermission(
            tenant_id=other_tenant.id,
            role_id=other_role.id,
            permission_id=other_perm_create.id,
        )
        db_session.add(other_rp2)
        await db_session.flush()

        other_user = User(
            tenant_id=other_tenant.id,
            email="outro@test.com",
            password_hash="fake",
            full_name="Outro User",
        )
        db_session.add(other_user)
        await db_session.flush()

        other_ur = UserRole(
            tenant_id=other_tenant.id,
            user_id=other_user.id,
            role_id=other_role.id,
        )
        db_session.add(other_ur)
        await db_session.flush()

        other_token = create_access_token(
            data={
                "sub": str(other_user.id),
                "tenant_id": other_tenant.id,
                "user_email": other_user.email,
            }
        )
        other_headers = {"Authorization": f"Bearer {other_token}"}

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": other_customer.id,
                "items": [{"product_id": other_product.id, "quantity": 1}],
            },
            headers=other_headers,
        )
        assert create_resp.status_code == 201
        other_order_id = create_resp.json()["id"]

        response = await client.get(
            f"/api/v1/orders/{other_order_id}",
            headers=authenticated_headers,
        )
        assert response.status_code in (403, 404)


class TestOrderInventoryIntegration:
    async def test_insufficient_stock_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        customer: Customer,
        product: Product,
        inventory: Inventory,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "order_insufficient",
            ["order.read", "order.create", "order.update"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": customer.id,
                "items": [{"product_id": product.id, "quantity": 200}],
            },
            headers=authenticated_headers,
        )
        order_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/orders/{order_id}/confirm",
            headers=authenticated_headers,
        )
        assert response.status_code == 409


async def _get_user(session: AsyncSession, tenant_id: int) -> User:

    stmt = select(User).where(
        User.tenant_id == tenant_id,
    )
    result = await session.execute(stmt)
    user = result.scalar_one()
    return user
