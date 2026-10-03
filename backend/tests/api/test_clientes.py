from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.db.models.cliente import Cliente
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


async def _create_role_with_perms(
    session: AsyncSession,
    empresa_id: int,
    name: str,
    perm_names: list[str],
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
    for pname in perm_names:
        perm = await _create_permission(session, empresa_id, pname)
        stmt_rp = select(RolePermission).where(
            RolePermission.empresa_id == empresa_id,
            RolePermission.role_id == role.id,
            RolePermission.permission_id == perm.id,
        )
        rp_result = await session.execute(stmt_rp)
        if rp_result.scalar_one_or_none() is None:
            rp = RolePermission(
                empresa_id=empresa_id,
                role_id=role.id,
                permission_id=perm.id,
            )
            session.add(rp)
            await session.flush()
    return role


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


async def _create_cliente_in_db(
    session: AsyncSession,
    empresa_id: int,
    name: str,
    document: str | None = None,
) -> Cliente:
    cliente = Cliente(
        empresa_id=empresa_id,
        name=name,
        document=document,
    )
    session.add(cliente)
    await session.flush()
    return cliente


@pytest.fixture
async def all_cliente_perms(
    db_session: AsyncSession,
    test_empresa: Empresa,
) -> Role:
    return await _create_role_with_perms(
        db_session,
        test_empresa.id,
        "cliente_admin",
        [
            "cliente.ler",
            "cliente.criar",
            "cliente.atualizar",
            "cliente.excluir",
        ],
    )


@pytest.fixture
async def admin_user(
    db_session: AsyncSession,
    test_empresa: Empresa,
    test_user: User,
    all_cliente_perms: Role,
) -> User:
    await _assign_role_to_user(
        db_session, test_empresa.id, test_user.id, all_cliente_perms.id
    )
    await db_session.commit()
    return test_user


@pytest.fixture
async def admin_headers(
    admin_user: User,
    test_empresa: Empresa,
) -> dict[str, str]:
    token = create_access_token(
        data={
            "sub": str(admin_user.id),
            "empresa_id": str(test_empresa.id),
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def other_empresa(db_session: AsyncSession) -> Empresa:
    empresa = Empresa(
        name="Outra Empresa",
        slug="other-cliente-empresa",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(empresa)
    await db_session.flush()
    return empresa


@pytest.fixture
async def other_empresa_user(
    db_session: AsyncSession,
    other_empresa: Empresa,
) -> User:
    user = User(
        empresa_id=other_empresa.id,
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
async def other_empresa_headers(
    db_session: AsyncSession,
    other_empresa_user: User,
    other_empresa: Empresa,
) -> dict[str, str]:
    role = await _create_role_with_perms(
        db_session,
        other_empresa.id,
        "other_cliente_all",
        [
            "cliente.ler",
            "cliente.criar",
            "cliente.atualizar",
            "cliente.excluir",
        ],
    )
    await _assign_role_to_user(
        db_session, other_empresa.id, other_empresa_user.id, role.id
    )
    await db_session.commit()
    token = create_access_token(
        data={
            "sub": str(other_empresa_user.id),
            "empresa_id": str(other_empresa.id),
        }
    )
    return {"Authorization": f"Bearer {token}"}


# --- CREATE ---


@pytest.mark.asyncio
async def test_create_cliente(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/clientes",
        headers=admin_headers,
        json={"name": "Joao Silva"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Joao Silva"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_cliente_without_permission(
    client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/clientes",
        headers=authenticated_headers,
        json={"name": "Joao Silva"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Acesso negado"


@pytest.mark.asyncio
async def test_create_cliente_duplicate_document(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    await _create_cliente_in_db(db_session, test_empresa.id, "Existing", "12345678901")
    await db_session.commit()

    response = await client.post(
        "/api/v1/clientes",
        headers=admin_headers,
        json={"name": "New Cliente", "document": "12345678901"},
    )
    assert response.status_code == 409


# --- LIST ---


@pytest.mark.asyncio
async def test_list_clientes_empty(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/clientes",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 20


@pytest.mark.asyncio
async def test_list_clientes_with_data(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    await _create_cliente_in_db(db_session, test_empresa.id, "Cliente A")
    await _create_cliente_in_db(db_session, test_empresa.id, "Cliente B")
    await db_session.commit()

    response = await client.get(
        "/api/v1/clientes",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_clientes_search(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    await _create_cliente_in_db(db_session, test_empresa.id, "Joao Silva")
    await _create_cliente_in_db(db_session, test_empresa.id, "Maria Santos")
    await db_session.commit()

    response = await client.get(
        "/api/v1/clientes",
        headers=admin_headers,
        params={"search": "Joao"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Joao Silva"


@pytest.mark.asyncio
async def test_list_clientes_pagination(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    for i in range(5):
        await _create_cliente_in_db(db_session, test_empresa.id, f"Cliente {i}")
    await db_session.commit()

    response = await client.get(
        "/api/v1/clientes",
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
async def test_list_clientes_sort(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    await _create_cliente_in_db(db_session, test_empresa.id, "Zebra")
    await _create_cliente_in_db(db_session, test_empresa.id, "Alpha")
    await db_session.commit()

    response = await client.get(
        "/api/v1/clientes",
        headers=admin_headers,
        params={"sort": "name", "order": "asc"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["name"] == "Alpha"
    assert data["items"][1]["name"] == "Zebra"


@pytest.mark.asyncio
async def test_list_clientes_sort_by_id_desc(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    first = await _create_cliente_in_db(db_session, test_empresa.id, "Primeiro")
    second = await _create_cliente_in_db(db_session, test_empresa.id, "Segundo")
    third = await _create_cliente_in_db(db_session, test_empresa.id, "Terceiro")
    # created_at invertido em relacao aos ids (id maior = created_at mais
    # antigo): se sort=id caisse no fallback de created_at, a ordem seria
    # a inversa da esperada.
    first.created_at = datetime(2026, 1, 3, tzinfo=UTC)
    second.created_at = datetime(2026, 1, 2, tzinfo=UTC)
    third.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    await db_session.commit()

    response = await client.get(
        "/api/v1/clientes",
        headers=admin_headers,
        params={"sort": "id", "order": "desc"},
    )
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [third.id, second.id, first.id]


@pytest.mark.asyncio
async def test_list_clientes_sort_by_id_asc(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    first = await _create_cliente_in_db(db_session, test_empresa.id, "Primeiro")
    second = await _create_cliente_in_db(db_session, test_empresa.id, "Segundo")
    third = await _create_cliente_in_db(db_session, test_empresa.id, "Terceiro")
    # created_at invertido em relacao aos ids (id maior = created_at mais
    # antigo): se sort=id caisse no fallback de created_at, a ordem seria
    # a inversa da esperada.
    first.created_at = datetime(2026, 1, 3, tzinfo=UTC)
    second.created_at = datetime(2026, 1, 2, tzinfo=UTC)
    third.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    await db_session.commit()

    response = await client.get(
        "/api/v1/clientes",
        headers=admin_headers,
        params={"sort": "id", "order": "asc"},
    )
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [first.id, second.id, third.id]


# --- GET BY ID ---


@pytest.mark.asyncio
async def test_get_cliente(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    cliente = await _create_cliente_in_db(db_session, test_empresa.id, "Joao Silva")
    await db_session.commit()

    response = await client.get(
        f"/api/v1/clientes/{cliente.id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Joao Silva"
    assert data["id"] == cliente.id


@pytest.mark.asyncio
async def test_get_cliente_not_found(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/clientes/99999",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_cliente_cross_empresa(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    other_empresa_headers: dict[str, str],
):
    cliente = await _create_cliente_in_db(db_session, test_empresa.id, "My Cliente")
    await db_session.commit()

    response = await client.get(
        f"/api/v1/clientes/{cliente.id}",
        headers=other_empresa_headers,
    )
    assert response.status_code == 404


# --- UPDATE ---


@pytest.mark.asyncio
async def test_update_cliente(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    cliente = await _create_cliente_in_db(db_session, test_empresa.id, "Joao Silva")
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/clientes/{cliente.id}",
        headers=admin_headers,
        json={"name": "Joao Updated"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Joao Updated"


@pytest.mark.asyncio
async def test_update_cliente_without_permission(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    authenticated_headers: dict[str, str],
):
    cliente = await _create_cliente_in_db(db_session, test_empresa.id, "Joao Silva")
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/clientes/{cliente.id}",
        headers=authenticated_headers,
        json={"name": "Joao Updated"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_cliente_not_found(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.patch(
        "/api/v1/clientes/99999",
        headers=admin_headers,
        json={"name": "Updated"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_cliente_cross_empresa(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    other_empresa_headers: dict[str, str],
):
    cliente = await _create_cliente_in_db(db_session, test_empresa.id, "My Cliente")
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/clientes/{cliente.id}",
        headers=other_empresa_headers,
        json={"name": "Hacked"},
    )
    assert response.status_code == 404


# --- DELETE ---


@pytest.mark.asyncio
async def test_delete_cliente(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    cliente = await _create_cliente_in_db(db_session, test_empresa.id, "Joao Silva")
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/clientes/{cliente.id}",
        headers=admin_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_deleted_cliente_not_in_list(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    cliente = await _create_cliente_in_db(db_session, test_empresa.id, "Joao Silva")
    await db_session.commit()

    await client.delete(
        f"/api/v1/clientes/{cliente.id}",
        headers=admin_headers,
    )

    response = await client.get(
        "/api/v1/clientes",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_deleted_cliente_not_found(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    cliente = await _create_cliente_in_db(db_session, test_empresa.id, "Joao Silva")
    await db_session.commit()

    await client.delete(
        f"/api/v1/clientes/{cliente.id}",
        headers=admin_headers,
    )

    response = await client.get(
        f"/api/v1/clientes/{cliente.id}",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_deleted_cliente_cannot_be_updated(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    cliente = await _create_cliente_in_db(db_session, test_empresa.id, "Joao Silva")
    await db_session.commit()

    await client.delete(
        f"/api/v1/clientes/{cliente.id}",
        headers=admin_headers,
    )

    response = await client.patch(
        f"/api/v1/clientes/{cliente.id}",
        headers=admin_headers,
        json={"name": "Updated"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_cliente_not_found(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.delete(
        "/api/v1/clientes/99999",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_cliente_cross_empresa(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    other_empresa_headers: dict[str, str],
):
    cliente = await _create_cliente_in_db(db_session, test_empresa.id, "My Cliente")
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/clientes/{cliente.id}",
        headers=other_empresa_headers,
    )
    assert response.status_code == 404


# --- UNAUTHENTICATED ---


@pytest.mark.asyncio
async def test_unauthenticated_access(client: AsyncClient):
    response = await client.get("/api/v1/clientes")
    assert response.status_code == 401


# --- ISOLAMENTO POR EMPRESA ---


@pytest.mark.asyncio
async def test_clientes_isolated_by_empresa(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    other_empresa: Empresa,
    admin_headers: dict[str, str],
    other_empresa_headers: dict[str, str],
):
    await _create_cliente_in_db(db_session, test_empresa.id, "Empresa A Cliente")
    await _create_cliente_in_db(db_session, other_empresa.id, "Empresa B Cliente")
    await db_session.commit()

    response_a = await client.get(
        "/api/v1/clientes",
        headers=admin_headers,
    )
    assert response_a.json()["total"] == 1
    assert response_a.json()["items"][0]["name"] == "Empresa A Cliente"

    response_b = await client.get(
        "/api/v1/clientes",
        headers=other_empresa_headers,
    )
    assert response_b.json()["total"] == 1
    assert response_b.json()["items"][0]["name"] == "Empresa B Cliente"
