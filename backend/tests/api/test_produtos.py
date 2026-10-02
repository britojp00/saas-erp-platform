import time
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.db.models.categoria import Categoria
from app.db.models.cliente import Cliente
from app.db.models.estoque import Estoque
from app.db.models.pedido import Pedido
from app.db.models.pedido_item import PedidoItem
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
    cost_price: Decimal | None = None,
    is_active: bool = True,
) -> Produto:
    produto = Produto(
        tenant_id=tenant_id,
        sku=sku,
        name=name,
        categoria_id=categoria_id,
        price=price,
        cost_price=cost_price,
        is_active=is_active,
    )
    session.add(produto)
    await session.flush()
    return produto


async def _create_estoque_in_db(
    session: AsyncSession,
    tenant_id: int,
    produto_id: int,
) -> Estoque:
    estoque = Estoque(
        tenant_id=tenant_id,
        produto_id=produto_id,
        quantity=Decimal("5.000"),
        reserved_quantity=Decimal("0.000"),
    )
    session.add(estoque)
    await session.flush()
    return estoque


async def _create_pedido_with_item(
    session: AsyncSession,
    tenant_id: int,
    produto_id: int,
) -> tuple[Pedido, PedidoItem]:
    cliente = Cliente(
        tenant_id=tenant_id,
        name="Test Cliente",
    )
    session.add(cliente)
    await session.flush()

    pedido = Pedido(
        tenant_id=tenant_id,
        numero_pedido=int(time.time() * 1000),
        cliente_id=cliente.id,
        status="RASCUNHO",
        total_amount=Decimal("100.00"),
    )
    session.add(pedido)
    await session.flush()

    pedido_item = PedidoItem(
        tenant_id=tenant_id,
        pedido_id=pedido.id,
        produto_id=produto_id,
        quantity=Decimal("2.000"),
        unit_price=Decimal("50.00"),
        total_price=Decimal("100.00"),
    )
    session.add(pedido_item)
    await session.flush()
    return pedido, pedido_item


@pytest.fixture
async def all_produto_perms(
    db_session: AsyncSession,
    test_tenant: Tenant,
) -> Role:
    return await _create_role_with_perms(
        db_session,
        test_tenant.id,
        "produto_admin",
        [
            "produto.ler",
            "produto.criar",
            "produto.atualizar",
            "produto.excluir",
        ],
    )


@pytest.fixture
async def admin_user(
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    all_produto_perms: Role,
) -> User:
    await _assign_role_to_user(
        db_session, test_tenant.id, test_user.id, all_produto_perms.id
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
async def other_tenant(db_session: AsyncSession) -> Tenant:
    tenant = Tenant(
        name="Other Tenant",
        slug="other-produto-tenant",
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
        "other_produto_all",
        [
            "produto.ler",
            "produto.criar",
            "produto.atualizar",
            "produto.excluir",
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


# --- CREATE ---


@pytest.mark.asyncio
async def test_create_produto(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/produtos",
        headers=admin_headers,
        json={
            "sku": "SKU-001",
            "name": "Laptop Pro",
            "price": "999.99",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "SKU-001"
    assert data["name"] == "Laptop Pro"
    assert Decimal(data["price"]) == Decimal("999.99")
    assert data["categoria_id"] is None
    assert data["description"] is None
    assert data["cost_price"] is None
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert data["deleted_at"] is None


@pytest.mark.asyncio
async def test_create_produto_with_all_fields(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Electronics")
    await db_session.commit()

    response = await client.post(
        "/api/v1/produtos",
        headers=admin_headers,
        json={
            "sku": "SKU-002",
            "name": "Laptop",
            "description": "A powerful laptop",
            "categoria_id": categoria.id,
            "price": "1299.99",
            "cost_price": "800.00",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "SKU-002"
    assert data["name"] == "Laptop"
    assert data["description"] == "A powerful laptop"
    assert data["categoria_id"] == categoria.id
    assert Decimal(data["price"]) == Decimal("1299.99")
    assert Decimal(data["cost_price"]) == Decimal("800.00")


@pytest.mark.asyncio
async def test_create_produto_without_permission(
    client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/produtos",
        headers=authenticated_headers,
        json={
            "sku": "SKU-003",
            "name": "Laptop",
            "price": "100.00",
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Acesso negado"


@pytest.mark.asyncio
async def test_create_produto_duplicate_sku(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    await _create_produto_in_db(db_session, test_tenant.id, "Laptop", "SKU-DUP")
    await db_session.commit()

    response = await client.post(
        "/api/v1/produtos",
        headers=admin_headers,
        json={
            "sku": "SKU-DUP",
            "name": "Another Laptop",
            "price": "100.00",
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_produto_missing_required_fields(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/produtos",
        headers=admin_headers,
        json={"name": "Laptop"},
    )
    assert response.status_code == 422

    response = await client.post(
        "/api/v1/produtos",
        headers=admin_headers,
        json={"sku": "SKU-004", "price": "100.00"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_produto_non_existent_categoria(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/produtos",
        headers=admin_headers,
        json={
            "sku": "SKU-005",
            "name": "Laptop",
            "price": "100.00",
            "categoria_id": 99999,
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_produto_cross_tenant_categoria(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    other_tenant: Tenant,
    admin_headers: dict[str, str],
):
    other_categoria = await _create_categoria_in_db(
        db_session, other_tenant.id, "Other Categoria"
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/produtos",
        headers=admin_headers,
        json={
            "sku": "SKU-006",
            "name": "Laptop",
            "price": "100.00",
            "categoria_id": other_categoria.id,
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_produto_deleted_categoria(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(
        db_session, test_tenant.id, "Deleted Categoria"
    )
    categoria.deleted_at = datetime.now(UTC)
    await db_session.commit()

    response = await client.post(
        "/api/v1/produtos",
        headers=admin_headers,
        json={
            "sku": "SKU-007",
            "name": "Laptop",
            "price": "100.00",
            "categoria_id": categoria.id,
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_produto_negative_price(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/produtos",
        headers=admin_headers,
        json={
            "sku": "SKU-008",
            "name": "Laptop",
            "price": "-10.00",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_produto_negative_cost_price(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/produtos",
        headers=admin_headers,
        json={
            "sku": "SKU-009",
            "name": "Laptop",
            "price": "100.00",
            "cost_price": "-5.00",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_produto_zero_price(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/produtos",
        headers=admin_headers,
        json={
            "sku": "SKU-010",
            "name": "Free Item",
            "price": "0.00",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert Decimal(data["price"]) == Decimal("0.00")


@pytest.mark.asyncio
async def test_create_produto_cost_price_higher_than_price(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/produtos",
        headers=admin_headers,
        json={
            "sku": "SKU-011",
            "name": "Laptop",
            "price": "100.00",
            "cost_price": "150.00",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert Decimal(data["cost_price"]) == Decimal("150.00")


# --- LIST ---


@pytest.mark.asyncio
async def test_list_produtos_empty(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/produtos",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 20


@pytest.mark.asyncio
async def test_list_produtos_with_data(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    await _create_produto_in_db(db_session, test_tenant.id, "Laptop", "SKU-L1")
    await _create_produto_in_db(db_session, test_tenant.id, "Mouse", "SKU-M1")
    await db_session.commit()

    response = await client.get(
        "/api/v1/produtos",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_produtos_search_by_name(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    await _create_produto_in_db(db_session, test_tenant.id, "Laptop Pro", "SKU-LP")
    await _create_produto_in_db(db_session, test_tenant.id, "Mouse Basic", "SKU-MB")
    await db_session.commit()

    response = await client.get(
        "/api/v1/produtos",
        headers=admin_headers,
        params={"search": "Laptop"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Laptop Pro"


@pytest.mark.asyncio
async def test_list_produtos_search_by_sku(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    await _create_produto_in_db(db_session, test_tenant.id, "Laptop", "SKU-ABC")
    await _create_produto_in_db(db_session, test_tenant.id, "Mouse", "SKU-XYZ")
    await db_session.commit()

    response = await client.get(
        "/api/v1/produtos",
        headers=admin_headers,
        params={"search": "ABC"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["sku"] == "SKU-ABC"


@pytest.mark.asyncio
async def test_list_produtos_pagination(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    for i in range(5):
        await _create_produto_in_db(
            db_session, test_tenant.id, f"Produto {i}", f"SKU-P{i}"
        )
    await db_session.commit()

    response = await client.get(
        "/api/v1/produtos",
        headers=admin_headers,
        params={"page": 1, "page_size": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2


@pytest.mark.asyncio
async def test_list_produtos_sort(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    await _create_produto_in_db(db_session, test_tenant.id, "Zebra", "SKU-Z")
    await _create_produto_in_db(db_session, test_tenant.id, "Alpha", "SKU-A")
    await db_session.commit()

    response = await client.get(
        "/api/v1/produtos",
        headers=admin_headers,
        params={"sort": "name", "order": "asc"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["name"] == "Alpha"
    assert data["items"][1]["name"] == "Zebra"


@pytest.mark.asyncio
async def test_list_produtos_filter_categoria(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    cat_a = await _create_categoria_in_db(db_session, test_tenant.id, "Cat A")
    cat_b = await _create_categoria_in_db(db_session, test_tenant.id, "Cat B")
    await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-F1", categoria_id=cat_a.id
    )
    await _create_produto_in_db(
        db_session, test_tenant.id, "Mouse", "SKU-F2", categoria_id=cat_b.id
    )
    await db_session.commit()

    response = await client.get(
        "/api/v1/produtos",
        headers=admin_headers,
        params={"categoria_id": cat_a.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["categoria_id"] == cat_a.id


@pytest.mark.asyncio
async def test_list_produtos_filter_is_active(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    await _create_produto_in_db(
        db_session, test_tenant.id, "Active", "SKU-ACT", is_active=True
    )
    await _create_produto_in_db(
        db_session, test_tenant.id, "Inactive", "SKU-INACT", is_active=False
    )
    await db_session.commit()

    response = await client.get(
        "/api/v1/produtos",
        headers=admin_headers,
        params={"is_active": "false"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Inactive"
    assert data["items"][0]["is_active"] is False


@pytest.mark.asyncio
async def test_list_produtos_without_permission(
    client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/produtos",
        headers=authenticated_headers,
    )
    assert response.status_code == 403


# --- GET BY ID ---


@pytest.mark.asyncio
async def test_get_produto(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-G1"
    )
    await db_session.commit()

    response = await client.get(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Laptop"
    assert data["sku"] == "SKU-G1"
    assert data["id"] == produto.id


@pytest.mark.asyncio
async def test_get_produto_not_found(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/produtos/99999",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_produto_cross_tenant(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    other_tenant_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Meu Produto", "SKU-GCT"
    )
    await db_session.commit()

    response = await client.get(
        f"/api/v1/produtos/{produto.id}",
        headers=other_tenant_headers,
    )
    assert response.status_code == 404


# --- UPDATE ---


@pytest.mark.asyncio
async def test_update_produto(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-U1"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
        json={"name": "Laptop Pro Max"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Laptop Pro Max"


@pytest.mark.asyncio
async def test_update_produto_sku(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-U2"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
        json={"sku": "SKU-NEW"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sku"] == "SKU-NEW"


@pytest.mark.asyncio
async def test_update_produto_price(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session,
        test_tenant.id,
        "Laptop",
        "SKU-U3",
        price=Decimal("500.00"),
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
        json={"price": "799.99"},
    )
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["price"]) == Decimal("799.99")


@pytest.mark.asyncio
async def test_update_produto_categoria(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "New Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-U4"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
        json={"categoria_id": categoria.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["categoria_id"] == categoria.id


@pytest.mark.asyncio
async def test_update_produto_remove_categoria(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session,
        test_tenant.id,
        "Laptop",
        "SKU-U5",
        categoria_id=categoria.id,
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
        json={"categoria_id": None},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["categoria_id"] is None


@pytest.mark.asyncio
async def test_update_produto_description(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-U6"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
        json={"description": "Updated description"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_update_produto_cost_price(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-U7"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
        json={"cost_price": "450.00"},
    )
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["cost_price"]) == Decimal("450.00")


@pytest.mark.asyncio
async def test_update_produto_is_active(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-U8", is_active=True
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_update_produto_without_permission(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    authenticated_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-U9"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=authenticated_headers,
        json={"name": "Hacked"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_produto_not_found(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.patch(
        "/api/v1/produtos/99999",
        headers=admin_headers,
        json={"name": "Updated"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_produto_cross_tenant(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    other_tenant_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Meu Produto", "SKU-UCT"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=other_tenant_headers,
        json={"name": "Hacked"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_produto_duplicate_sku(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    await _create_produto_in_db(db_session, test_tenant.id, "Laptop", "SKU-EXISTING")
    other = await _create_produto_in_db(
        db_session, test_tenant.id, "Mouse", "SKU-OTHER"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{other.id}",
        headers=admin_headers,
        json={"sku": "SKU-EXISTING"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_produto_same_sku_no_conflict(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-SAME"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
        json={"sku": "SKU-SAME"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_produto_non_existent_categoria(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-NC"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
        json={"categoria_id": 99999},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_produto_cross_tenant_categoria(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    other_tenant: Tenant,
    admin_headers: dict[str, str],
):
    other_categoria = await _create_categoria_in_db(
        db_session, other_tenant.id, "Other Cat"
    )
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-XC"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
        json={"categoria_id": other_categoria.id},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_produto_deleted_categoria(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Deleted Cat")
    categoria.deleted_at = datetime.now(UTC)
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-DC"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
        json={"categoria_id": categoria.id},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_produto_negative_price(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-NP"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
        json={"price": "-10.00"},
    )
    assert response.status_code == 422


# --- DELETE ---


@pytest.mark.asyncio
async def test_delete_produto(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-D1"
    )
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_deleted_produto_not_in_list(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-D2"
    )
    await db_session.commit()

    await client.delete(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
    )

    response = await client.get(
        "/api/v1/produtos",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_deleted_produto_not_found(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-D3"
    )
    await db_session.commit()

    await client.delete(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
    )

    response = await client.get(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_deleted_produto_cannot_be_updated(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-D4"
    )
    await db_session.commit()

    await client.delete(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
    )

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
        json={"name": "Updated"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_produto_not_found(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.delete(
        "/api/v1/produtos/99999",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_produto_cross_tenant(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    other_tenant_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Meu Produto", "SKU-DCT"
    )
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/produtos/{produto.id}",
        headers=other_tenant_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_produto_without_permission(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    authenticated_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-DNP"
    )
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/produtos/{produto.id}",
        headers=authenticated_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_produto_with_estoque_blocked(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-DINV"
    )
    await _create_estoque_in_db(db_session, test_tenant.id, produto.id)
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_produto_with_pedido_itens_blocked(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-DORD"
    )
    await _create_pedido_with_item(db_session, test_tenant.id, produto.id)
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
    )
    assert response.status_code == 409


# --- MULTI-TENANCY ---


@pytest.mark.asyncio
async def test_produtos_isolated_by_tenant(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    other_tenant: Tenant,
    admin_headers: dict[str, str],
    other_tenant_headers: dict[str, str],
):
    await _create_produto_in_db(
        db_session, test_tenant.id, "Produto Tenant A", "SKU-TA"
    )
    await _create_produto_in_db(
        db_session, other_tenant.id, "Produto Tenant B", "SKU-TB"
    )
    await db_session.commit()

    response_a = await client.get(
        "/api/v1/produtos",
        headers=admin_headers,
    )
    assert response_a.json()["total"] == 1
    assert response_a.json()["items"][0]["name"] == "Produto Tenant A"

    response_b = await client.get(
        "/api/v1/produtos",
        headers=other_tenant_headers,
    )
    assert response_b.json()["total"] == 1
    assert response_b.json()["items"][0]["name"] == "Produto Tenant B"


@pytest.mark.asyncio
async def test_same_sku_different_tenants(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    other_tenant: Tenant,
    admin_headers: dict[str, str],
    other_tenant_headers: dict[str, str],
):
    await _create_produto_in_db(db_session, test_tenant.id, "Laptop", "SKU-SAME-SKU")
    await _create_produto_in_db(db_session, other_tenant.id, "Laptop", "SKU-SAME-SKU")
    await db_session.commit()

    response_a = await client.get(
        "/api/v1/produtos",
        headers=admin_headers,
    )
    assert response_a.json()["total"] == 1

    response_b = await client.get(
        "/api/v1/produtos",
        headers=other_tenant_headers,
    )
    assert response_b.json()["total"] == 1


@pytest.mark.asyncio
async def test_unauthenticated_access(client: AsyncClient):
    response = await client.get("/api/v1/produtos")
    assert response.status_code == 401


# --- DECIMAL PRECISION ---


@pytest.mark.asyncio
async def test_create_produto_decimal_precision(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/produtos",
        headers=admin_headers,
        json={
            "sku": "SKU-DEC",
            "name": "Produto Preciso",
            "price": "1234567890.12",
            "cost_price": "9876543210.98",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert Decimal(data["price"]) == Decimal("1234567890.12")
    assert Decimal(data["cost_price"]) == Decimal("9876543210.98")


@pytest.mark.asyncio
async def test_update_produto_cost_price_to_null(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session,
        test_tenant.id,
        "Laptop",
        "SKU-CN",
        cost_price=Decimal("500.00"),
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
        json={"cost_price": None},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cost_price"] is None


# --- IS_ACTIVE ---


@pytest.mark.asyncio
async def test_create_produto_inactive(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/produtos",
        headers=admin_headers,
        json={
            "sku": "SKU-INACT",
            "name": "Produto Inativo",
            "price": "50.00",
            "is_active": False,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_update_produto_activate_deactivated(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Laptop", "SKU-ACTV", is_active=False
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/produtos/{produto.id}",
        headers=admin_headers,
        json={"is_active": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True
