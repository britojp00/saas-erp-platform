from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.db.models.empresa import Empresa
from app.db.models.permission import Permission
from app.db.models.role import Role
from app.db.models.role_permission import RolePermission
from app.db.models.user import User
from app.db.models.user_role import UserRole


async def _create_permission(
    session: AsyncSession,
    empresa_id: int,
    name: str,
) -> Permission:
    stmt = select(Permission).where(
        Permission.empresa_id == empresa_id,
        Permission.name == name,
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    perm = Permission(empresa_id=empresa_id, name=name)
    session.add(perm)
    await session.flush()
    return perm


async def _create_role(
    session: AsyncSession,
    empresa_id: int,
    name: str,
) -> Role:
    stmt = select(Role).where(
        Role.empresa_id == empresa_id,
        Role.name == name,
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    role = Role(empresa_id=empresa_id, name=name)
    session.add(role)
    await session.flush()
    return role


async def _assign_permission(
    session: AsyncSession,
    empresa_id: int,
    role_id: int,
    permission_id: int,
) -> None:
    stmt = select(RolePermission).where(
        RolePermission.empresa_id == empresa_id,
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id,
    )
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        return
    rp = RolePermission(
        empresa_id=empresa_id,
        role_id=role_id,
        permission_id=permission_id,
    )
    session.add(rp)
    await session.flush()


async def _assign_role_to_user(
    session: AsyncSession,
    empresa_id: int,
    user_id: int,
    role_id: int,
) -> None:
    stmt = select(UserRole).where(
        UserRole.empresa_id == empresa_id,
        UserRole.user_id == user_id,
        UserRole.role_id == role_id,
    )
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        return
    ur = UserRole(
        empresa_id=empresa_id,
        user_id=user_id,
        role_id=role_id,
    )
    session.add(ur)
    await session.flush()


@pytest.mark.asyncio
async def test_me_returns_roles_and_permissions(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    test_user: User,
    authenticated_headers: dict[str, str],
):
    role = await _create_role(db_session, test_empresa.id, "admin")
    perm = await _create_permission(db_session, test_empresa.id, "cliente.ler")
    await _assign_permission(db_session, test_empresa.id, role.id, perm.id)
    await _assign_role_to_user(db_session, test_empresa.id, test_user.id, role.id)
    await db_session.commit()

    response = await client.get(
        "/api/v1/auth/me",
        headers=authenticated_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "admin" in data["roles"]
    assert "cliente.ler" in data["permissions"]


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
    test_empresa: Empresa,
    test_user: User,
):
    role_read = await _create_permission(db_session, test_empresa.id, "role.read")
    role = await _create_role(db_session, test_empresa.id, "viewer")
    await _assign_permission(db_session, test_empresa.id, role.id, role_read.id)
    await _assign_role_to_user(db_session, test_empresa.id, test_user.id, role.id)
    await db_session.commit()

    token = create_access_token(
        data={
            "sub": str(test_user.id),
            "empresa_id": str(test_empresa.id),
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
    test_empresa: Empresa,
    test_user: User,
):
    role = await _create_role(db_session, test_empresa.id, "noperm")
    perm = await _create_permission(db_session, test_empresa.id, "cliente.ler")
    await _assign_permission(db_session, test_empresa.id, role.id, perm.id)
    await _assign_role_to_user(db_session, test_empresa.id, test_user.id, role.id)
    await db_session.commit()

    token = create_access_token(
        data={
            "sub": str(test_user.id),
            "empresa_id": str(test_empresa.id),
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
async def test_cross_empresa_cannot_see_roles(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    test_user: User,
):
    other_empresa = Empresa(
        name="Outra Empresa",
        slug="other-empresa-rbac",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(other_empresa)
    await db_session.flush()

    other_role = await _create_role(db_session, other_empresa.id, "other-admin")
    other_perm = await _create_permission(db_session, other_empresa.id, "role.read")
    await _assign_permission(db_session, other_empresa.id, other_role.id, other_perm.id)

    my_role = await _create_role(db_session, test_empresa.id, "my-viewer")
    my_perm = await _create_permission(db_session, test_empresa.id, "role.read")
    await _assign_permission(db_session, test_empresa.id, my_role.id, my_perm.id)
    await _assign_role_to_user(db_session, test_empresa.id, test_user.id, my_role.id)
    await db_session.commit()

    token = create_access_token(
        data={
            "sub": str(test_user.id),
            "empresa_id": str(test_empresa.id),
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
    test_empresa: Empresa,
    test_user: User,
):
    perm_a = await _create_permission(db_session, test_empresa.id, "cliente.ler")
    role = await _create_role(db_session, test_empresa.id, "partial")
    await _assign_permission(db_session, test_empresa.id, role.id, perm_a.id)
    await _assign_role_to_user(db_session, test_empresa.id, test_user.id, role.id)
    await db_session.commit()

    token = create_access_token(
        data={
            "sub": str(test_user.id),
            "empresa_id": str(test_empresa.id),
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
