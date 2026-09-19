from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
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


async def _create_role(
    session: AsyncSession,
    tenant_id: int,
    name: str,
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
    return role


async def _assign_permission(
    session: AsyncSession,
    tenant_id: int,
    role_id: int,
    permission_id: int,
) -> None:
    stmt = select(RolePermission).where(
        RolePermission.tenant_id == tenant_id,
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id,
    )
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        return
    rp = RolePermission(
        tenant_id=tenant_id,
        role_id=role_id,
        permission_id=permission_id,
    )
    session.add(rp)
    await session.flush()


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


@pytest.mark.asyncio
async def test_me_returns_roles_and_permissions(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    authenticated_headers: dict[str, str],
):
    role = await _create_role(db_session, test_tenant.id, "admin")
    perm = await _create_permission(db_session, test_tenant.id, "customer.read")
    await _assign_permission(db_session, test_tenant.id, role.id, perm.id)
    await _assign_role_to_user(db_session, test_tenant.id, test_user.id, role.id)
    await db_session.commit()

    response = await client.get(
        "/api/v1/auth/me",
        headers=authenticated_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "admin" in data["roles"]
    assert "customer.read" in data["permissions"]


@pytest.mark.asyncio
async def test_me_user_without_roles(
    client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/auth/me",
        headers=authenticated_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["roles"] == []
    assert data["permissions"] == []


@pytest.mark.asyncio
async def test_roles_endpoint_with_permission(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    role_read = await _create_permission(db_session, test_tenant.id, "role.read")
    role = await _create_role(db_session, test_tenant.id, "viewer")
    await _assign_permission(db_session, test_tenant.id, role.id, role_read.id)
    await _assign_role_to_user(db_session, test_tenant.id, test_user.id, role.id)
    await db_session.commit()

    token = create_access_token(
        data={
            "sub": str(test_user.id),
            "tenant_id": str(test_tenant.id),
        }
    )
    response = await client.get(
        "/api/v1/auth/roles",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(r["name"] == "viewer" for r in data)


@pytest.mark.asyncio
async def test_roles_endpoint_without_permission(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    role = await _create_role(db_session, test_tenant.id, "noperm")
    perm = await _create_permission(db_session, test_tenant.id, "customer.read")
    await _assign_permission(db_session, test_tenant.id, role.id, perm.id)
    await _assign_role_to_user(db_session, test_tenant.id, test_user.id, role.id)
    await db_session.commit()

    token = create_access_token(
        data={
            "sub": str(test_user.id),
            "tenant_id": str(test_tenant.id),
        }
    )
    response = await client.get(
        "/api/v1/auth/roles",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Acesso negado"


@pytest.mark.asyncio
async def test_roles_endpoint_without_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/roles")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cross_tenant_cannot_see_roles(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    other_tenant = Tenant(
        name="Other Tenant",
        slug="other-tenant-rbac",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(other_tenant)
    await db_session.flush()

    other_role = await _create_role(db_session, other_tenant.id, "other-admin")
    other_perm = await _create_permission(db_session, other_tenant.id, "role.read")
    await _assign_permission(db_session, other_tenant.id, other_role.id, other_perm.id)

    my_role = await _create_role(db_session, test_tenant.id, "my-viewer")
    my_perm = await _create_permission(db_session, test_tenant.id, "role.read")
    await _assign_permission(db_session, test_tenant.id, my_role.id, my_perm.id)
    await _assign_role_to_user(db_session, test_tenant.id, test_user.id, my_role.id)
    await db_session.commit()

    token = create_access_token(
        data={
            "sub": str(test_user.id),
            "tenant_id": str(test_tenant.id),
        }
    )
    response = await client.get(
        "/api/v1/auth/roles",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert not any(r["name"] == "other-admin" for r in data)
    assert any(r["name"] == "my-viewer" for r in data)


@pytest.mark.asyncio
async def test_multiple_permissions_required(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    perm_a = await _create_permission(db_session, test_tenant.id, "customer.read")
    role = await _create_role(db_session, test_tenant.id, "partial")
    await _assign_permission(db_session, test_tenant.id, role.id, perm_a.id)
    await _assign_role_to_user(db_session, test_tenant.id, test_user.id, role.id)
    await db_session.commit()

    token = create_access_token(
        data={
            "sub": str(test_user.id),
            "tenant_id": str(test_tenant.id),
        }
    )
    response = await client.get(
        "/api/v1/auth/roles",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_me_response_has_roles_and_permissions_fields(
    client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/auth/me",
        headers=authenticated_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "roles" in data
    assert "permissions" in data
    assert isinstance(data["roles"], list)
    assert isinstance(data["permissions"], list)
    assert "password_hash" not in data
