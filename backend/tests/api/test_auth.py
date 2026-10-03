from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.db.models.empresa import Empresa
from app.db.models.user import User


@pytest.mark.asyncio
async def test_login_success(
    client: AsyncClient,
    test_user: User,
    test_empresa: Empresa,
):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(
    client: AsyncClient,
    test_user: User,
):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas"


@pytest.mark.asyncio
async def test_login_nonexistent_email(
    client: AsyncClient,
    test_user: User,
):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "anypassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas"


@pytest.mark.asyncio
async def test_login_inactive_user(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
):
    user = User(
        empresa_id=test_empresa.id,
        email="inactive@example.com",
        password_hash=get_password_hash("password123"),
        full_name="Inactive User",
        is_active=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "password123"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas"


@pytest.mark.asyncio
async def test_login_deleted_user(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
):
    user = User(
        empresa_id=test_empresa.id,
        email="deleted@example.com",
        password_hash=get_password_hash("password123"),
        full_name="Deleted User",
        is_active=True,
        deleted_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "deleted@example.com", "password": "password123"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas"


@pytest.mark.asyncio
async def test_login_inactive_empresa(
    client: AsyncClient,
    db_session: AsyncSession,
):
    empresa = Empresa(
        name="Empresa Inativa",
        slug="inactive-empresa",
        is_active=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(empresa)
    await db_session.flush()

    user = User(
        empresa_id=empresa.id,
        email="user@inactive.com",
        password_hash=get_password_hash("password123"),
        full_name="Usuario Empresa Inativa",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@inactive.com", "password": "password123"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas"


@pytest.mark.asyncio
async def test_me_with_valid_token(
    client: AsyncClient,
    test_user: User,
    authenticated_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/auth/me",
        headers=authenticated_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert data["is_active"] is True
    assert "id" in data
    assert "empresa_id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_me_without_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalidtoken123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_expired_token(
    client: AsyncClient,
    test_user: User,
    test_empresa: Empresa,
):
    token = create_access_token(
        data={
            "sub": str(test_user.id),
            "empresa_id": str(test_empresa.id),
        },
        expires_delta=timedelta(seconds=-1),
    )
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cross_empresa_user_id_mismatch(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
):
    other_empresa = Empresa(
        name="Outra Empresa",
        slug="other-empresa",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(other_empresa)
    await db_session.flush()

    other_user = User(
        empresa_id=other_empresa.id,
        email="other@example.com",
        password_hash=get_password_hash("password123"),
        full_name="Other User",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(other_user)
    await db_session.flush()

    token = create_access_token(
        data={
            "sub": str(other_user.id),
            "empresa_id": str(test_empresa.id),
        }
    )
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
