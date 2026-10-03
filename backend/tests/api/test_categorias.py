from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.db.models.categoria import Categoria
from app.db.models.empresa import Empresa
from app.db.models.permission import Permission
from app.db.models.produto import Produto
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


async def _create_categoria_in_db(
    session: AsyncSession,
    empresa_id: int,
    name: str,
    parent_id: int | None = None,
) -> Categoria:
    categoria = Categoria(
        empresa_id=empresa_id,
        name=name,
        parent_id=parent_id,
    )
    session.add(categoria)
    await session.flush()
    return categoria


async def _create_produto_in_db(
    session: AsyncSession,
    empresa_id: int,
    name: str,
    categoria_id: int | None = None,
) -> Produto:
    produto = Produto(
        empresa_id=empresa_id,
        sku=f"SKU-{name.upper().replace(' ', '-')}",
        name=name,
        price=10.00,
        categoria_id=categoria_id,
    )
    session.add(produto)
    await session.flush()
    return produto


@pytest.fixture
async def all_categoria_perms(
    db_session: AsyncSession,
    test_empresa: Empresa,
) -> Role:
    return await _create_role_with_perms(
        db_session,
        test_empresa.id,
        "categoria_admin",
        [
            "categoria.ler",
            "categoria.criar",
            "categoria.atualizar",
            "categoria.excluir",
        ],
    )


@pytest.fixture
async def admin_user(
    db_session: AsyncSession,
    test_empresa: Empresa,
    test_user: User,
    all_categoria_perms: Role,
) -> User:
    await _assign_role_to_user(
        db_session, test_empresa.id, test_user.id, all_categoria_perms.id
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
        slug="other-categoria-empresa",
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
    db_session: AsyncClient,
    other_empresa_user: User,
    other_empresa: Empresa,
) -> dict[str, str]:
    role = await _create_role_with_perms(
        db_session,
        other_empresa.id,
        "other_categoria_all",
        [
            "categoria.ler",
            "categoria.criar",
            "categoria.atualizar",
            "categoria.excluir",
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
async def test_create_categoria(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/categorias",
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
async def test_create_categoria_with_description(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/categorias",
        headers=admin_headers,
        json={"name": "Electronics", "description": "Electronic devices"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Electronic devices"


@pytest.mark.asyncio
async def test_create_categoria_with_parent(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    parent = await _create_categoria_in_db(db_session, test_empresa.id, "Parent")
    await db_session.commit()

    response = await client.post(
        "/api/v1/categorias",
        headers=admin_headers,
        json={"name": "Child", "parent_id": parent.id},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["parent_id"] == parent.id


@pytest.mark.asyncio
async def test_create_categoria_without_permission(
    client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/categorias",
        headers=authenticated_headers,
        json={"name": "Electronics"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Acesso negado"


@pytest.mark.asyncio
async def test_create_categoria_duplicate_name(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    await _create_categoria_in_db(db_session, test_empresa.id, "Electronics")
    await db_session.commit()

    response = await client.post(
        "/api/v1/categorias",
        headers=admin_headers,
        json={"name": "Electronics"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_categoria_parent_not_found(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.post(
        "/api/v1/categorias",
        headers=admin_headers,
        json={"name": "Child", "parent_id": 99999},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_categoria_self_reference(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(db_session, test_empresa.id, "Categoria")
    await db_session.commit()

    response = await client.post(
        "/api/v1/categorias",
        headers=admin_headers,
        json={"name": "Child", "parent_id": categoria.id},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_categoria_cross_empresa_parent(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    other_empresa: Empresa,
    admin_headers: dict[str, str],
):
    other_parent = await _create_categoria_in_db(
        db_session, other_empresa.id, "Other Parent"
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/categorias",
        headers=admin_headers,
        json={"name": "Child", "parent_id": other_parent.id},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_categoria_deep_hierarchy(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    parent = await _create_categoria_in_db(db_session, test_empresa.id, "Level 1")
    child = await _create_categoria_in_db(
        db_session, test_empresa.id, "Level 2", parent_id=parent.id
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/categorias",
        headers=admin_headers,
        json={"name": "Level 3", "parent_id": child.id},
    )
    assert response.status_code == 201


# --- LIST ---


@pytest.mark.asyncio
async def test_list_categorias_empty(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/categorias",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 20


@pytest.mark.asyncio
async def test_list_categorias_with_data(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    await _create_categoria_in_db(db_session, test_empresa.id, "Categoria A")
    await _create_categoria_in_db(db_session, test_empresa.id, "Categoria B")
    await db_session.commit()

    response = await client.get(
        "/api/v1/categorias",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_categorias_search(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    await _create_categoria_in_db(db_session, test_empresa.id, "Electronics")
    await _create_categoria_in_db(db_session, test_empresa.id, "Clothing")
    await db_session.commit()

    response = await client.get(
        "/api/v1/categorias",
        headers=admin_headers,
        params={"search": "Electro"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Electronics"


@pytest.mark.asyncio
async def test_list_categorias_pagination(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    for i in range(5):
        await _create_categoria_in_db(db_session, test_empresa.id, f"Categoria {i}")
    await db_session.commit()

    response = await client.get(
        "/api/v1/categorias",
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
async def test_list_categorias_sort(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    await _create_categoria_in_db(db_session, test_empresa.id, "Zebra")
    await _create_categoria_in_db(db_session, test_empresa.id, "Alpha")
    await db_session.commit()

    response = await client.get(
        "/api/v1/categorias",
        headers=admin_headers,
        params={"sort": "name", "order": "asc"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["name"] == "Alpha"
    assert data["items"][1]["name"] == "Zebra"


@pytest.mark.asyncio
async def test_list_categorias_without_permission(
    client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/categorias",
        headers=authenticated_headers,
    )
    assert response.status_code == 403


# --- GET BY ID ---


@pytest.mark.asyncio
async def test_get_categoria(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(
        db_session, test_empresa.id, "Electronics"
    )
    await db_session.commit()

    response = await client.get(
        f"/api/v1/categorias/{categoria.id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Electronics"
    assert data["id"] == categoria.id


@pytest.mark.asyncio
async def test_get_categoria_not_found(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/categorias/99999",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_categoria_cross_empresa(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    other_empresa_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(
        db_session, test_empresa.id, "My Categoria"
    )
    await db_session.commit()

    response = await client.get(
        f"/api/v1/categorias/{categoria.id}",
        headers=other_empresa_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_categoria_without_permission(
    client: AsyncClient,
    authenticated_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/categorias/1",
        headers=authenticated_headers,
    )
    assert response.status_code == 403


# --- UPDATE ---


@pytest.mark.asyncio
async def test_update_categoria(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(
        db_session, test_empresa.id, "Electronics"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categorias/{categoria.id}",
        headers=admin_headers,
        json={"name": "Consumer Electronics"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Consumer Electronics"


@pytest.mark.asyncio
async def test_update_categoria_description(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(
        db_session, test_empresa.id, "Electronics"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categorias/{categoria.id}",
        headers=admin_headers,
        json={"description": "Updated description"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_update_categoria_clear_description(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(
        db_session, test_empresa.id, "Electronics"
    )
    categoria.description = "Some description"
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categorias/{categoria.id}",
        headers=admin_headers,
        json={"description": None},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] is None


@pytest.mark.asyncio
async def test_update_categoria_change_parent(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    parent_a = await _create_categoria_in_db(db_session, test_empresa.id, "Parent A")
    parent_b = await _create_categoria_in_db(db_session, test_empresa.id, "Parent B")
    child = await _create_categoria_in_db(
        db_session, test_empresa.id, "Child", parent_id=parent_a.id
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categorias/{child.id}",
        headers=admin_headers,
        json={"parent_id": parent_b.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["parent_id"] == parent_b.id


@pytest.mark.asyncio
async def test_update_categoria_remove_parent(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    parent = await _create_categoria_in_db(db_session, test_empresa.id, "Parent")
    child = await _create_categoria_in_db(
        db_session, test_empresa.id, "Child", parent_id=parent.id
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categorias/{child.id}",
        headers=admin_headers,
        json={"parent_id": None},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["parent_id"] is None


@pytest.mark.asyncio
async def test_update_categoria_without_permission(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    authenticated_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(
        db_session, test_empresa.id, "Electronics"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categorias/{categoria.id}",
        headers=authenticated_headers,
        json={"name": "Updated"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_categoria_not_found(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.patch(
        "/api/v1/categorias/99999",
        headers=admin_headers,
        json={"name": "Updated"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_categoria_cross_empresa(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    other_empresa_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(
        db_session, test_empresa.id, "My Categoria"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categorias/{categoria.id}",
        headers=other_empresa_headers,
        json={"name": "Hacked"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_categoria_self_reference(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(db_session, test_empresa.id, "Categoria")
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categorias/{categoria.id}",
        headers=admin_headers,
        json={"parent_id": categoria.id},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_categoria_cycle_prevention(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    grandparent = await _create_categoria_in_db(db_session, test_empresa.id, "GP")
    parent = await _create_categoria_in_db(
        db_session, test_empresa.id, "P", parent_id=grandparent.id
    )
    child = await _create_categoria_in_db(
        db_session, test_empresa.id, "C", parent_id=parent.id
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categorias/{grandparent.id}",
        headers=admin_headers,
        json={"parent_id": child.id},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_categoria_duplicate_name(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    await _create_categoria_in_db(db_session, test_empresa.id, "Electronics")
    other = await _create_categoria_in_db(db_session, test_empresa.id, "Clothing")
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categorias/{other.id}",
        headers=admin_headers,
        json={"name": "Electronics"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_categoria_parent_not_found(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(db_session, test_empresa.id, "Categoria")
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categorias/{categoria.id}",
        headers=admin_headers,
        json={"parent_id": 99999},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_categoria_name_same_no_conflict(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(
        db_session, test_empresa.id, "Electronics"
    )
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/categorias/{categoria.id}",
        headers=admin_headers,
        json={"name": "Electronics"},
    )
    assert response.status_code == 200


# --- DELETE ---


@pytest.mark.asyncio
async def test_delete_categoria(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(
        db_session, test_empresa.id, "Electronics"
    )
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/categorias/{categoria.id}",
        headers=admin_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_deleted_categoria_not_in_list(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(
        db_session, test_empresa.id, "Electronics"
    )
    await db_session.commit()

    await client.delete(
        f"/api/v1/categorias/{categoria.id}",
        headers=admin_headers,
    )

    response = await client.get(
        "/api/v1/categorias",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_deleted_categoria_not_found(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(
        db_session, test_empresa.id, "Electronics"
    )
    await db_session.commit()

    await client.delete(
        f"/api/v1/categorias/{categoria.id}",
        headers=admin_headers,
    )

    response = await client.get(
        f"/api/v1/categorias/{categoria.id}",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_deleted_categoria_cannot_be_updated(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(
        db_session, test_empresa.id, "Electronics"
    )
    await db_session.commit()

    await client.delete(
        f"/api/v1/categorias/{categoria.id}",
        headers=admin_headers,
    )

    response = await client.patch(
        f"/api/v1/categorias/{categoria.id}",
        headers=admin_headers,
        json={"name": "Updated"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_categoria_not_found(
    client: AsyncClient,
    admin_headers: dict[str, str],
):
    response = await client.delete(
        "/api/v1/categorias/99999",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_categoria_cross_empresa(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    other_empresa_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(
        db_session, test_empresa.id, "My Categoria"
    )
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/categorias/{categoria.id}",
        headers=other_empresa_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_categoria_with_children_blocked(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    parent = await _create_categoria_in_db(db_session, test_empresa.id, "Parent")
    await _create_categoria_in_db(
        db_session, test_empresa.id, "Child", parent_id=parent.id
    )
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/categorias/{parent.id}",
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_categoria_with_produtos_blocked(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(
        db_session, test_empresa.id, "Electronics"
    )
    await _create_produto_in_db(
        db_session, test_empresa.id, "Laptop", categoria_id=categoria.id
    )
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/categorias/{categoria.id}",
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_categoria_without_permission(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    authenticated_headers: dict[str, str],
):
    categoria = await _create_categoria_in_db(
        db_session, test_empresa.id, "Electronics"
    )
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/categorias/{categoria.id}",
        headers=authenticated_headers,
    )
    assert response.status_code == 403


# --- HIERARCHY ---


@pytest.mark.asyncio
async def test_create_multiple_children(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    parent = await _create_categoria_in_db(db_session, test_empresa.id, "Parent")
    await db_session.commit()

    await client.post(
        "/api/v1/categorias",
        headers=admin_headers,
        json={"name": "Child 1", "parent_id": parent.id},
    )
    response = await client.post(
        "/api/v1/categorias",
        headers=admin_headers,
        json={"name": "Child 2", "parent_id": parent.id},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_delete_child_before_parent(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    admin_headers: dict[str, str],
):
    parent = await _create_categoria_in_db(db_session, test_empresa.id, "Parent")
    child = await _create_categoria_in_db(
        db_session, test_empresa.id, "Child", parent_id=parent.id
    )
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/categorias/{child.id}",
        headers=admin_headers,
    )
    assert response.status_code == 204


# --- UNAUTHENTICATED ---


@pytest.mark.asyncio
async def test_unauthenticated_access(client: AsyncClient):
    response = await client.get("/api/v1/categorias")
    assert response.status_code == 401


# --- ISOLAMENTO POR EMPRESA ---


@pytest.mark.asyncio
async def test_categorias_isolated_by_empresa(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    other_empresa: Empresa,
    admin_headers: dict[str, str],
    other_empresa_headers: dict[str, str],
):
    await _create_categoria_in_db(db_session, test_empresa.id, "Empresa A Categoria")
    await _create_categoria_in_db(db_session, other_empresa.id, "Empresa B Categoria")
    await db_session.commit()

    response_a = await client.get(
        "/api/v1/categorias",
        headers=admin_headers,
    )
    assert response_a.json()["total"] == 1
    assert response_a.json()["items"][0]["name"] == "Empresa A Categoria"

    response_b = await client.get(
        "/api/v1/categorias",
        headers=other_empresa_headers,
    )
    assert response_b.json()["total"] == 1
    assert response_b.json()["items"][0]["name"] == "Empresa B Categoria"


@pytest.mark.asyncio
async def test_same_name_different_empresas(
    client: AsyncClient,
    db_session: AsyncSession,
    test_empresa: Empresa,
    other_empresa: Empresa,
    admin_headers: dict[str, str],
    other_empresa_headers: dict[str, str],
):
    await _create_categoria_in_db(db_session, test_empresa.id, "Electronics")
    await _create_categoria_in_db(db_session, other_empresa.id, "Electronics")
    await db_session.commit()

    response_a = await client.post(
        "/api/v1/categorias",
        headers=admin_headers,
        json={"name": "Electronics"},
    )
    assert response_a.status_code == 409

    response_b = await client.post(
        "/api/v1/categorias",
        headers=other_empresa_headers,
        json={"name": "Electronics"},
    )
    assert response_b.status_code == 409
