from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.db.models.audit_log import AuditLog
from app.db.models.permission import Permission
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


ALL_AUDIT_PERMS = [
    "customer.read",
    "customer.create",
    "customer.update",
    "customer.delete",
    "category.read",
    "category.create",
    "category.update",
    "category.delete",
    "product.read",
    "product.create",
    "product.update",
    "product.delete",
    "inventory.read",
    "inventory.update",
    "order.read",
    "order.create",
    "order.update",
    "order.cancel",
    "role.read",
]


@pytest.fixture
async def all_perms_role(
    db_session: AsyncSession,
    test_tenant: Tenant,
) -> Role:
    return await _create_role_with_perms(
        db_session,
        test_tenant.id,
        "audit_admin",
        ALL_AUDIT_PERMS,
    )


@pytest.fixture
async def admin_user(
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    all_perms_role: Role,
) -> User:
    await _assign_role_to_user(
        db_session, test_tenant.id, test_user.id, all_perms_role.id
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
        slug="other-audit-tenant",
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
        email="other-audit@example.com",
        full_name="Other Audit User",
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
    other_tenant_user: User,
    other_tenant: Tenant,
    db_session: AsyncSession,
) -> dict[str, str]:
    role = await _create_role_with_perms(
        db_session,
        other_tenant.id,
        "other_audit_all",
        ALL_AUDIT_PERMS,
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


# --- LIST ---


@pytest.mark.asyncio
async def test_list_audit_logs_empty(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/audit-logs",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 20


@pytest.mark.asyncio
async def test_list_audit_logs_without_permission(
    client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/audit-logs",
        headers=authenticated_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_audit_logs_without_auth(
    client: AsyncClient,
):
    response = await client.get("/api/v1/audit-logs")
    assert response.status_code == 401


# --- AUDIT FROM CUSTOMER OPERATIONS ---


@pytest.mark.asyncio
async def test_customer_create_generates_audit(
    client: AsyncClient,
    admin_headers: dict[str, str],
    db_session: AsyncSession,
    test_tenant: Tenant,
):
    response = await client.post(
        "/api/v1/customers",
        headers=admin_headers,
        json={"name": "Audit Customer"},
    )
    assert response.status_code == 201
    customer_id = response.json()["id"]

    stmt = select(AuditLog).where(
        AuditLog.tenant_id == test_tenant.id,
        AuditLog.action == "CUSTOMER_CREATE",
        AuditLog.entity_id == customer_id,
    )
    result = await db_session.execute(stmt)
    audit = result.scalar_one_or_none()
    assert audit is not None
    assert audit.entity_type == "customer"
    assert audit.new_values is not None
    assert audit.new_values["name"] == "Audit Customer"


@pytest.mark.asyncio
async def test_customer_update_generates_audit(
    client: AsyncClient,
    admin_headers: dict[str, str],
    db_session: AsyncSession,
    test_tenant: Tenant,
):
    create_resp = await client.post(
        "/api/v1/customers",
        headers=admin_headers,
        json={"name": "Original Name"},
    )
    customer_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/customers/{customer_id}",
        headers=admin_headers,
        json={"name": "Updated Name"},
    )
    assert response.status_code == 200

    stmt = select(AuditLog).where(
        AuditLog.tenant_id == test_tenant.id,
        AuditLog.action == "CUSTOMER_UPDATE",
        AuditLog.entity_id == customer_id,
    )
    result = await db_session.execute(stmt)
    audit = result.scalar_one_or_none()
    assert audit is not None
    assert audit.old_values is not None
    assert audit.old_values["name"] == "Original Name"
    assert audit.new_values["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_customer_delete_generates_audit(
    client: AsyncClient,
    admin_headers: dict[str, str],
    db_session: AsyncSession,
    test_tenant: Tenant,
):
    create_resp = await client.post(
        "/api/v1/customers",
        headers=admin_headers,
        json={"name": "To Delete"},
    )
    customer_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/v1/customers/{customer_id}",
        headers=admin_headers,
    )
    assert response.status_code == 204

    stmt = select(AuditLog).where(
        AuditLog.tenant_id == test_tenant.id,
        AuditLog.action == "CUSTOMER_DELETE",
        AuditLog.entity_id == customer_id,
    )
    result = await db_session.execute(stmt)
    audit = result.scalar_one_or_none()
    assert audit is not None
    assert audit.old_values is not None
    assert audit.old_values["name"] == "To Delete"


# --- AUDIT FROM CATEGORY OPERATIONS ---


@pytest.mark.asyncio
async def test_category_create_generates_audit(
    client: AsyncClient,
    admin_headers: dict[str, str],
    db_session: AsyncSession,
    test_tenant: Tenant,
):
    response = await client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Audit Category"},
    )
    assert response.status_code == 201
    category_id = response.json()["id"]

    stmt = select(AuditLog).where(
        AuditLog.tenant_id == test_tenant.id,
        AuditLog.action == "CATEGORY_CREATE",
        AuditLog.entity_id == category_id,
    )
    result = await db_session.execute(stmt)
    audit = result.scalar_one_or_none()
    assert audit is not None
    assert audit.entity_type == "category"


# --- AUDIT FROM PRODUCT OPERATIONS ---


@pytest.mark.asyncio
async def test_product_create_generates_audit(
    client: AsyncClient,
    admin_headers: dict[str, str],
    db_session: AsyncSession,
    test_tenant: Tenant,
):
    response = await client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={
            "sku": "AUDIT-001",
            "name": "Audit Product",
            "price": 99.90,
        },
    )
    assert response.status_code == 201
    product_id = response.json()["id"]

    stmt = select(AuditLog).where(
        AuditLog.tenant_id == test_tenant.id,
        AuditLog.action == "PRODUCT_CREATE",
        AuditLog.entity_id == product_id,
    )
    result = await db_session.execute(stmt)
    audit = result.scalar_one_or_none()
    assert audit is not None
    assert audit.entity_type == "product"
    assert audit.new_values is not None
    assert audit.new_values["sku"] == "AUDIT-001"


# --- AUDIT CONTENT ---


@pytest.mark.asyncio
async def test_audit_log_has_correct_user_id(
    client: AsyncClient,
    admin_headers: dict[str, str],
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    await client.post(
        "/api/v1/customers",
        headers=admin_headers,
        json={"name": "User Check"},
    )

    stmt = select(AuditLog).where(
        AuditLog.tenant_id == test_tenant.id,
        AuditLog.action == "CUSTOMER_CREATE",
    )
    result = await db_session.execute(stmt)
    audit = result.scalar_one_or_none()
    assert audit is not None
    assert audit.user_id == test_user.id


@pytest.mark.asyncio
async def test_audit_log_has_correct_tenant_id(
    client: AsyncClient,
    admin_headers: dict[str, str],
    db_session: AsyncSession,
    test_tenant: Tenant,
):
    await client.post(
        "/api/v1/customers",
        headers=admin_headers,
        json={"name": "Tenant Check"},
    )

    stmt = select(AuditLog).where(
        AuditLog.action == "CUSTOMER_CREATE",
    )
    result = await db_session.execute(stmt)
    audit = result.scalar_one_or_none()
    assert audit is not None
    assert audit.tenant_id == test_tenant.id


# --- SECURITY ---


@pytest.mark.asyncio
async def test_password_not_in_audit_log(
    client: AsyncClient,
    admin_headers: dict[str, str],
    db_session: AsyncSession,
    test_tenant: Tenant,
):
    await client.post(
        "/api/v1/customers",
        headers=admin_headers,
        json={"name": "Security Check"},
    )

    stmt = select(AuditLog).where(
        AuditLog.tenant_id == test_tenant.id,
    )
    result = await db_session.execute(stmt)
    audits = list(result.scalars().all())
    for audit in audits:
        if audit.old_values:
            assert "password" not in str(audit.old_values).lower()
            assert "password_hash" not in str(audit.old_values).lower()
        if audit.new_values:
            assert "password" not in str(audit.new_values).lower()
            assert "password_hash" not in str(audit.new_values).lower()


# --- MULTI-TENANCY ---


@pytest.mark.asyncio
async def test_tenant_isolation(
    client: AsyncClient,
    admin_headers: dict[str, str],
    other_tenant_headers: dict[str, str],
    db_session: AsyncSession,
    test_tenant: Tenant,
):
    await client.post(
        "/api/v1/customers",
        headers=admin_headers,
        json={"name": "Tenant A Customer"},
    )

    response = await client.get(
        "/api/v1/audit-logs",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

    other_response = await client.get(
        "/api/v1/audit-logs",
        headers=other_tenant_headers,
    )
    assert other_response.status_code == 200
    other_data = other_response.json()
    assert other_data["total"] == 0


# --- APPEND-ONLY ---


@pytest.mark.asyncio
async def test_no_update_endpoint(client: AsyncClient):
    response = await client.patch("/api/v1/audit-logs/1")
    assert response.status_code in [405, 404]


@pytest.mark.asyncio
async def test_no_delete_endpoint(client: AsyncClient):
    response = await client.delete("/api/v1/audit-logs/1")
    assert response.status_code in [405, 404]


@pytest.mark.asyncio
async def test_no_post_endpoint(client: AsyncClient):
    response = await client.post("/api/v1/audit-logs", json={})
    assert response.status_code in [405, 422]


# --- PAGINATION & FILTERS ---


@pytest.mark.asyncio
async def test_list_with_pagination(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    await client.post(
        "/api/v1/customers",
        headers=admin_headers,
        json={"name": "Paginated"},
    )

    response = await client.get(
        "/api/v1/audit-logs",
        headers=admin_headers,
        params={"page": 1, "page_size": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 2
    assert data["page"] == 1
    assert data["page_size"] == 2


@pytest.mark.asyncio
async def test_list_with_action_filter(
    client: AsyncClient,
    admin_headers: dict[str, str],
    db_session: AsyncSession,
    test_tenant: Tenant,
):
    await client.post(
        "/api/v1/customers",
        headers=admin_headers,
        json={"name": "Filter Test"},
    )

    response = await client.get(
        "/api/v1/audit-logs",
        headers=admin_headers,
        params={"action": "CUSTOMER_CREATE"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["action"] == "CUSTOMER_CREATE"


@pytest.mark.asyncio
async def test_list_with_entity_type_filter(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    await client.post(
        "/api/v1/customers",
        headers=admin_headers,
        json={"name": "Entity Filter"},
    )

    response = await client.get(
        "/api/v1/audit-logs",
        headers=admin_headers,
        params={"entity_type": "customer"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["entity_type"] == "customer"


@pytest.mark.asyncio
async def test_list_invalid_sort_falls_back_to_default(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/audit-logs",
        headers=admin_headers,
        params={"sort": "invalid_field", "order": "invalid_order"},
    )
    assert response.status_code == 200


# --- ATOMICITY ---


@pytest.mark.asyncio
async def test_failed_operation_no_audit_log(
    client: AsyncClient,
    admin_headers: dict[str, str],
    db_session: AsyncSession,
    test_tenant: Tenant,
):
    count_before = 0
    stmt = select(AuditLog).where(AuditLog.tenant_id == test_tenant.id)
    result = await db_session.execute(stmt)
    count_before = len(list(result.scalars().all()))

    response = await client.post(
        "/api/v1/customers",
        headers=admin_headers,
        json={"name": ""},
    )
    assert response.status_code == 422

    stmt_after = select(AuditLog).where(AuditLog.tenant_id == test_tenant.id)
    result_after = await db_session.execute(stmt_after)
    count_after = len(list(result_after.scalars().all()))

    assert count_after == count_before


# --- LOGIN AUDIT ---


@pytest.mark.asyncio
async def test_login_success_generates_audit(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200

    stmt = select(AuditLog).where(
        AuditLog.tenant_id == test_tenant.id,
        AuditLog.action == "LOGIN_SUCCESS",
    )
    result = await db_session.execute(stmt)
    audit = result.scalar_one_or_none()
    assert audit is not None
    assert audit.entity_type == "user"


@pytest.mark.asyncio
async def test_login_failure_wrong_password_generates_audit(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401

    stmt = select(AuditLog).where(
        AuditLog.tenant_id == test_tenant.id,
        AuditLog.action == "LOGIN_FAILURE",
    )
    result = await db_session.execute(stmt)
    audit = result.scalar_one_or_none()
    assert audit is not None
    assert audit.user_id == test_user.id
    assert audit.description == "Invalid password"
