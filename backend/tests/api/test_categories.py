from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.db.models.category import Category
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


async def _create_category_in_db(
    session: AsyncSession,
    tenant_id: int,
    name: str,
    parent_id: int | None = None,
) -> Category:
    category = Category(
        tenant_id=tenant_id,
        name=name,
        parent_id=parent_id,
    )
    session.add(category)
    await session.flush()
    return category


async def _create_product_in_db(
    session: AsyncSession,
    tenant_id: int,
    name: str,
    category_id: int | None = None,
) -> Product:
    product = Product(
        tenant_id=tenant_id,
        sku=f"SKU-{name.upper().replace(' ', '-')}",
        name=name,
        price=10.00,
        category_id=category_id,
    )
    session.add(product)
    await session.flush()
    return product


@pytest.fixture
async def all_category_perms(
    db_session: AsyncSession,
    test_tenant: Tenant,
) -> Role:
    return await _create_role_with_perms(
        db_session,
        test_tenant.id,
        "category_admin",
        [
            "category.read",
            "category.create",
            "category.update",
            "category.delete",
        ],
    )


@pytest.fixture
async def admin_user(
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    all_category_perms: Role,
) -> User:
    await _assign_role_to_user(
        db_session, test_tenant.id, test_user.id, all_category_perms.id
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
        slug="other-category-tenant",
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
    db_session: AsyncClient,
    other_tenant_user: User,
    other_tenant: Tenant,
) -> dict[str, str]:
    role = await _create_role_with_perms(
        db_session,
        other_tenant.id,
        "other_category_all",
        [
            "category.read",
            "category.create",
            "category.update",
            "category.delete",
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
async def test_create_category(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Electronics"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Electronics"
    assert data["parent_id"] is None
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert data["deleted_at"] is None


@pytest.mark.asyncio
async def test_create_category_with_description(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Electronics", "description": "Electronic devices"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Electronic devices"


@pytest.mark.asyncio
async def test_create_category_with_parent(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    parent = await _create_category_in_db(db_session, test_tenant.id, "Parent")
    await db_session.commit()

    response = await client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Child", "parent_id": parent.id},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["parent_id"] == parent.id


@pytest.mark.asyncio
async def test_create_category_without_permission(
    client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/categories",
        headers=authenticated_headers,
        json={"name": "Electronics"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Acesso negado"


@pytest.mark.asyncio
async def test_create_category_duplicate_name(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    await _create_category_in_db(db_session, test_tenant.id, "Electronics")
    await db_session.commit()

    response = await client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Electronics"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_category_parent_not_found(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Child", "parent_id": 99999},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_category_self_reference(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "Category")
    await db_session.commit()

    response = await client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Child", "parent_id": category.id},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_category_cross_tenant_parent(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    other_tenant: Tenant,
    admin_headers: dict[str, str],
):
    other_parent = await _create_category_in_db(
        db_session, other_tenant.id, "Other Parent"
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Child", "parent_id": other_parent.id},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_category_deep_hierarchy(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    parent = await _create_category_in_db(db_session, test_tenant.id, "Level 1")
    child = await _create_category_in_db(
        db_session, test_tenant.id, "Level 2", parent_id=parent.id
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Level 3", "parent_id": child.id},
    )
    assert response.status_code == 201


# --- LIST ---


@pytest.mark.asyncio
async def test_list_categories_empty(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/categories",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 20


@pytest.mark.asyncio
async def test_list_categories_with_data(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    await _create_category_in_db(db_session, test_tenant.id, "Category A")
    await _create_category_in_db(db_session, test_tenant.id, "Category B")
    await db_session.commit()

    response = await client.get(
        "/api/v1/categories",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_categories_search(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    await _create_category_in_db(db_session, test_tenant.id, "Electronics")
    await _create_category_in_db(db_session, test_tenant.id, "Clothing")
    await db_session.commit()

    response = await client.get(
        "/api/v1/categories",
        headers=admin_headers,
        params={"search": "Electro"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Electronics"


@pytest.mark.asyncio
async def test_list_categories_pagination(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    for i in range(5):
        await _create_category_in_db(db_session, test_tenant.id, f"Category {i}")
    await db_session.commit()

    response = await client.get(
        "/api/v1/categories",
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
async def test_list_categories_sort(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    await _create_category_in_db(db_session, test_tenant.id, "Zebra")
    await _create_category_in_db(db_session, test_tenant.id, "Alpha")
    await db_session.commit()

    response = await client.get(
        "/api/v1/categories",
        headers=admin_headers,
        params={"sort": "name", "order": "asc"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["name"] == "Alpha"
    assert data["items"][1]["name"] == "Zebra"


@pytest.mark.asyncio
async def test_list_categories_without_permission(
    client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/categories",
        headers=authenticated_headers,
    )
    assert response.status_code == 403


# --- GET BY ID ---


@pytest.mark.asyncio
async def test_get_category(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "Electronics")
    await db_session.commit()

    response = await client.get(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Electronics"
    assert data["id"] == category.id


@pytest.mark.asyncio
async def test_get_category_not_found(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/categories/99999",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_category_cross_tenant(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    other_tenant_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "My Category")
    await db_session.commit()

    response = await client.get(
        f"/api/v1/categories/{category.id}",
        headers=other_tenant_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_category_without_permission(
    client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/categories/1",
        headers=authenticated_headers,
    )
    assert response.status_code == 403


# --- UPDATE ---


@pytest.mark.asyncio
async def test_update_category(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "Electronics")
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
        json={"name": "Consumer Electronics"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Consumer Electronics"


@pytest.mark.asyncio
async def test_update_category_description(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "Electronics")
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
        json={"description": "Updated description"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_update_category_clear_description(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "Electronics")
    category.description = "Some description"
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
        json={"description": None},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] is None


@pytest.mark.asyncio
async def test_update_category_change_parent(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    parent_a = await _create_category_in_db(db_session, test_tenant.id, "Parent A")
    parent_b = await _create_category_in_db(db_session, test_tenant.id, "Parent B")
    child = await _create_category_in_db(
        db_session, test_tenant.id, "Child", parent_id=parent_a.id
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categories/{child.id}",
        headers=admin_headers,
        json={"parent_id": parent_b.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["parent_id"] == parent_b.id


@pytest.mark.asyncio
async def test_update_category_remove_parent(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    parent = await _create_category_in_db(db_session, test_tenant.id, "Parent")
    child = await _create_category_in_db(
        db_session, test_tenant.id, "Child", parent_id=parent.id
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categories/{child.id}",
        headers=admin_headers,
        json={"parent_id": None},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["parent_id"] is None


@pytest.mark.asyncio
async def test_update_category_without_permission(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    authenticated_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "Electronics")
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categories/{category.id}",
        headers=authenticated_headers,
        json={"name": "Updated"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_category_not_found(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.patch(
        "/api/v1/categories/99999",
        headers=admin_headers,
        json={"name": "Updated"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_category_cross_tenant(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    other_tenant_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "My Category")
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categories/{category.id}",
        headers=other_tenant_headers,
        json={"name": "Hacked"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_category_self_reference(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "Category")
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
        json={"parent_id": category.id},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_category_cycle_prevention(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    grandparent = await _create_category_in_db(db_session, test_tenant.id, "GP")
    parent = await _create_category_in_db(
        db_session, test_tenant.id, "P", parent_id=grandparent.id
    )
    child = await _create_category_in_db(
        db_session, test_tenant.id, "C", parent_id=parent.id
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categories/{grandparent.id}",
        headers=admin_headers,
        json={"parent_id": child.id},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_category_duplicate_name(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    await _create_category_in_db(db_session, test_tenant.id, "Electronics")
    other = await _create_category_in_db(db_session, test_tenant.id, "Clothing")
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categories/{other.id}",
        headers=admin_headers,
        json={"name": "Electronics"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_category_parent_not_found(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "Category")
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
        json={"parent_id": 99999},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_category_name_same_no_conflict(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "Electronics")
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
        json={"name": "Electronics"},
    )
    assert response.status_code == 200


# --- DELETE ---


@pytest.mark.asyncio
async def test_delete_category(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "Electronics")
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_deleted_category_not_in_list(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "Electronics")
    await db_session.commit()

    await client.delete(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
    )

    response = await client.get(
        "/api/v1/categories",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_deleted_category_not_found(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "Electronics")
    await db_session.commit()

    await client.delete(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
    )

    response = await client.get(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_deleted_category_cannot_be_updated(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "Electronics")
    await db_session.commit()

    await client.delete(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
    )

    response = await client.patch(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
        json={"name": "Updated"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_category_not_found(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.delete(
        "/api/v1/categories/99999",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_category_cross_tenant(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    other_tenant_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "My Category")
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/categories/{category.id}",
        headers=other_tenant_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_category_with_children_blocked(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    parent = await _create_category_in_db(db_session, test_tenant.id, "Parent")
    await _create_category_in_db(
        db_session, test_tenant.id, "Child", parent_id=parent.id
    )
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/categories/{parent.id}",
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_category_with_products_blocked(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "Electronics")
    await _create_product_in_db(
        db_session, test_tenant.id, "Laptop", category_id=category.id
    )
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/categories/{category.id}",
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_category_without_permission(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    authenticated_headers: dict[str, str],
):
    category = await _create_category_in_db(db_session, test_tenant.id, "Electronics")
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/categories/{category.id}",
        headers=authenticated_headers,
    )
    assert response.status_code == 403


# --- HIERARCHY ---


@pytest.mark.asyncio
async def test_create_multiple_children(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    parent = await _create_category_in_db(db_session, test_tenant.id, "Parent")
    await db_session.commit()

    await client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Child 1", "parent_id": parent.id},
    )
    response = await client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Child 2", "parent_id": parent.id},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_delete_child_before_parent(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
):
    parent = await _create_category_in_db(db_session, test_tenant.id, "Parent")
    child = await _create_category_in_db(
        db_session, test_tenant.id, "Child", parent_id=parent.id
    )
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/categories/{child.id}",
        headers=admin_headers,
    )
    assert response.status_code == 204


# --- UNAUTHENTICATED ---


@pytest.mark.asyncio
async def test_unauthenticated_access(client: AsyncClient):
    response = await client.get("/api/v1/categories")
    assert response.status_code == 401


# --- TENANT ISOLATION ---


@pytest.mark.asyncio
async def test_categories_isolated_by_tenant(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    other_tenant: Tenant,
    admin_headers: dict[str, str],
    other_tenant_headers: dict[str, str],
):
    await _create_category_in_db(db_session, test_tenant.id, "Tenant A Category")
    await _create_category_in_db(db_session, other_tenant.id, "Tenant B Category")
    await db_session.commit()

    response_a = await client.get(
        "/api/v1/categories",
        headers=admin_headers,
    )
    assert response_a.json()["total"] == 1
    assert response_a.json()["items"][0]["name"] == "Tenant A Category"

    response_b = await client.get(
        "/api/v1/categories",
        headers=other_tenant_headers,
    )
    assert response_b.json()["total"] == 1
    assert response_b.json()["items"][0]["name"] == "Tenant B Category"


@pytest.mark.asyncio
async def test_same_name_different_tenants(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    other_tenant: Tenant,
    admin_headers: dict[str, str],
    other_tenant_headers: dict[str, str],
):
    await _create_category_in_db(db_session, test_tenant.id, "Electronics")
    await _create_category_in_db(db_session, other_tenant.id, "Electronics")
    await db_session.commit()

    response_a = await client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Electronics"},
    )
    assert response_a.status_code == 409

    response_b = await client.post(
        "/api/v1/categories",
        headers=other_tenant_headers,
        json={"name": "Electronics"},
    )
    assert response_b.status_code == 409
