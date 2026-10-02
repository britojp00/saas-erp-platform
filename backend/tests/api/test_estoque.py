from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.db.models.categoria import Categoria
from app.db.models.estoque import Estoque
from app.db.models.movimentacao_estoque import MovimentacaoEstoque, TipoMovimentacao
from app.db.models.permission import Permission
from app.db.models.produto import Produto
from app.db.models.reserva_estoque import ReservaEstoque, StatusReserva
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


async def _create_estoque_in_db(
    session: AsyncSession,
    tenant_id: int,
    produto_id: int,
    quantity: Decimal = Decimal("100.000"),
    reserved_quantity: Decimal = Decimal("0.000"),
) -> Estoque:
    estoque = Estoque(
        tenant_id=tenant_id,
        produto_id=produto_id,
        quantity=quantity,
        reserved_quantity=reserved_quantity,
    )
    session.add(estoque)
    await session.flush()
    return estoque


async def _create_movimentacao_in_db(
    session: AsyncSession,
    tenant_id: int,
    produto_id: int,
    tipo_movimentacao: str = "ENTRADA",
    quantity: Decimal = Decimal("10.000"),
    idempotency_key: str = "test-key",
) -> MovimentacaoEstoque:
    movimentacao = MovimentacaoEstoque(
        tenant_id=tenant_id,
        produto_id=produto_id,
        tipo_movimentacao=TipoMovimentacao(tipo_movimentacao),
        quantity=quantity,
        idempotency_key=idempotency_key,
    )
    session.add(movimentacao)
    await session.flush()
    return movimentacao


async def _create_reserva_in_db(
    session: AsyncSession,
    tenant_id: int,
    produto_id: int,
    quantity: Decimal = Decimal("5.000"),
    status: StatusReserva = StatusReserva.ATIVA,
    idempotency_key: str = "test-reserva-key",
) -> ReservaEstoque:
    reserva = ReservaEstoque(
        tenant_id=tenant_id,
        produto_id=produto_id,
        quantity=quantity,
        status=status,
        idempotency_key=idempotency_key,
    )
    session.add(reserva)
    await session.flush()
    return reserva


@pytest.fixture
async def all_estoque_perms(
    db_session: AsyncSession,
    test_tenant: Tenant,
) -> Role:
    return await _create_role_with_perms(
        db_session,
        test_tenant.id,
        "estoque_admin",
        [
            "estoque.ler",
            "estoque.atualizar",
        ],
    )


@pytest.fixture
async def read_only_estoque_perms(
    db_session: AsyncSession,
    test_tenant: Tenant,
) -> Role:
    return await _create_role_with_perms(
        db_session,
        test_tenant.id,
        "estoque_reader",
        [
            "estoque.ler",
        ],
    )


@pytest.fixture
async def admin_user(
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    all_estoque_perms: Role,
) -> User:
    await _assign_role_to_user(
        db_session, test_tenant.id, test_user.id, all_estoque_perms.id
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
    read_only_estoque_perms: Role,
) -> User:
    await _assign_role_to_user(
        db_session, test_tenant.id, test_user.id, read_only_estoque_perms.id
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
        slug="other-estoque-tenant",
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
        "other_estoque_all",
        [
            "estoque.ler",
            "estoque.atualizar",
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


# --- MOVIMENTACAO ---


@pytest.mark.asyncio
async def test_create_entrada_movimentacao(
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
        "/api/v1/estoque/movimentacoes",
        json={
            "produto_id": produto.id,
            "tipo_movimentacao": "ENTRADA",
            "quantity": "50.000",
            "reference": "PO-001",
            "idempotency_key": "in-movimentacao-1",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tipo_movimentacao"] == "ENTRADA"
    assert data["quantity"] == "50.000"
    assert data["produto_id"] == produto.id
    assert data["reference"] == "PO-001"


@pytest.mark.asyncio
async def test_create_saida_movimentacao(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto B", "SKU-B", categoria.id
    )
    await _create_estoque_in_db(db_session, test_tenant.id, produto.id)
    await db_session.commit()

    response = await client.post(
        "/api/v1/estoque/movimentacoes",
        json={
            "produto_id": produto.id,
            "tipo_movimentacao": "SAIDA",
            "quantity": "10.000",
            "idempotency_key": "out-movimentacao-1",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tipo_movimentacao"] == "SAIDA"
    assert data["quantity"] == "10.000"


@pytest.mark.asyncio
async def test_ajuste_movimentacao(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto C", "SKU-C", categoria.id
    )
    await _create_estoque_in_db(db_session, test_tenant.id, produto.id)
    await db_session.commit()

    response = await client.post(
        "/api/v1/estoque/movimentacoes",
        json={
            "produto_id": produto.id,
            "tipo_movimentacao": "AJUSTE",
            "quantity": "75.000",
            "notes": "Stock count correction",
            "idempotency_key": "adj-movimentacao-1",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tipo_movimentacao"] == "AJUSTE"


@pytest.mark.asyncio
async def test_movimentacao_updates_saldo(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto D", "SKU-D", categoria.id
    )
    await _create_estoque_in_db(
        db_session, test_tenant.id, produto.id, quantity=Decimal("50.000")
    )
    await db_session.commit()

    await client.post(
        "/api/v1/estoque/movimentacoes",
        json={
            "produto_id": produto.id,
            "tipo_movimentacao": "ENTRADA",
            "quantity": "25.000",
            "idempotency_key": "in-25",
        },
        headers=admin_headers,
    )

    response = await client.get(
        f"/api/v1/estoque/{produto.id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == "75.000"


@pytest.mark.asyncio
async def test_saida_movimentacao_insufficient_stock(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto E", "SKU-E", categoria.id
    )
    await _create_estoque_in_db(
        db_session, test_tenant.id, produto.id, quantity=Decimal("5.000")
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/estoque/movimentacoes",
        json={
            "produto_id": produto.id,
            "tipo_movimentacao": "SAIDA",
            "quantity": "10.000",
            "idempotency_key": "out-10",
        },
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_saida_movimentacao_cannot_consume_reserved(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto F", "SKU-F", categoria.id
    )
    await _create_estoque_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        quantity=Decimal("10.000"),
        reserved_quantity=Decimal("5.000"),
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/estoque/movimentacoes",
        json={
            "produto_id": produto.id,
            "tipo_movimentacao": "SAIDA",
            "quantity": "8.000",
            "idempotency_key": "out-8",
        },
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_ajuste_leaves_reserved_exceeds_quantity(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto G", "SKU-G", categoria.id
    )
    await _create_estoque_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        quantity=Decimal("10.000"),
        reserved_quantity=Decimal("5.000"),
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/estoque/movimentacoes",
        json={
            "produto_id": produto.id,
            "tipo_movimentacao": "AJUSTE",
            "quantity": "3.000",
            "idempotency_key": "adj-3",
        },
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_idempotent_movimentacao_returns_same(
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
        "/api/v1/estoque/movimentacoes",
        json={
            "produto_id": produto.id,
            "tipo_movimentacao": "ENTRADA",
            "quantity": "10.000",
            "idempotency_key": "idempotent-1",
        },
        headers=admin_headers,
    )
    assert response1.status_code == 201

    response2 = await client.post(
        "/api/v1/estoque/movimentacoes",
        json={
            "produto_id": produto.id,
            "tipo_movimentacao": "ENTRADA",
            "quantity": "20.000",
            "idempotency_key": "idempotent-1",
        },
        headers=admin_headers,
    )
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_list_movimentacoes(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto I", "SKU-I", categoria.id
    )
    await _create_movimentacao_in_db(
        db_session, test_tenant.id, produto.id, "ENTRADA", Decimal("10.000"), "key-1"
    )
    await _create_movimentacao_in_db(
        db_session, test_tenant.id, produto.id, "SAIDA", Decimal("5.000"), "key-2"
    )
    await db_session.commit()

    response = await client.get(
        "/api/v1/estoque/movimentacoes/list",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


# --- RESERVA ---


@pytest.mark.asyncio
async def test_create_reserva(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto J", "SKU-J", categoria.id
    )
    await _create_estoque_in_db(db_session, test_tenant.id, produto.id)
    await db_session.commit()

    response = await client.post(
        "/api/v1/estoque/reservas",
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
    assert data["status"] == "ATIVA"
    assert data["quantity"] == "5.000"
    assert data["produto_id"] == produto.id


@pytest.mark.asyncio
async def test_reserva_updates_reserved_quantity(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto K", "SKU-K", categoria.id
    )
    await _create_estoque_in_db(
        db_session, test_tenant.id, produto.id, quantity=Decimal("20.000")
    )
    await db_session.commit()

    await client.post(
        "/api/v1/estoque/reservas",
        json={
            "produto_id": produto.id,
            "quantity": "7.000",
            "idempotency_key": "res-7",
        },
        headers=admin_headers,
    )

    response = await client.get(
        f"/api/v1/estoque/{produto.id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["reserved_quantity"] == "7.000"
    assert data["quantity"] == "20.000"


@pytest.mark.asyncio
async def test_reserva_insufficient_stock(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto L", "SKU-L", categoria.id
    )
    await _create_estoque_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        quantity=Decimal("10.000"),
        reserved_quantity=Decimal("8.000"),
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/estoque/reservas",
        json={
            "produto_id": produto.id,
            "quantity": "5.000",
            "idempotency_key": "res-over",
        },
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_reserva_inactive_produto(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto M", "SKU-M", categoria.id, is_active=False
    )
    await _create_estoque_in_db(db_session, test_tenant.id, produto.id)
    await db_session.commit()

    response = await client.post(
        "/api/v1/estoque/reservas",
        json={
            "produto_id": produto.id,
            "quantity": "2.000",
            "idempotency_key": "res-inactive",
        },
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_confirm_reserva(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto N", "SKU-N", categoria.id
    )
    estoque = await _create_estoque_in_db(
        db_session, test_tenant.id, produto.id, quantity=Decimal("20.000")
    )
    reserva = await _create_reserva_in_db(
        db_session, test_tenant.id, produto.id, Decimal("5.000")
    )
    estoque.reserved_quantity = Decimal("5.000")
    await db_session.commit()

    response = await client.post(
        f"/api/v1/estoque/reservas/{reserva.id}/confirmar",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CONFIRMADA"
    assert data["confirmed_at"] is not None

    response2 = await client.get(
        f"/api/v1/estoque/{produto.id}",
        headers=admin_headers,
    )
    assert response2.json()["reserved_quantity"] == "0.000"


@pytest.mark.asyncio
async def test_release_reserva(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto O", "SKU-O", categoria.id
    )
    estoque = await _create_estoque_in_db(
        db_session, test_tenant.id, produto.id, quantity=Decimal("20.000")
    )
    reserva = await _create_reserva_in_db(
        db_session, test_tenant.id, produto.id, Decimal("5.000")
    )
    estoque.reserved_quantity = Decimal("5.000")
    await db_session.commit()

    response = await client.post(
        f"/api/v1/estoque/reservas/{reserva.id}/liberar",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "LIBERADA"
    assert data["released_at"] is not None


@pytest.mark.asyncio
async def test_cancel_reserva(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto P", "SKU-P", categoria.id
    )
    estoque = await _create_estoque_in_db(
        db_session, test_tenant.id, produto.id, quantity=Decimal("20.000")
    )
    reserva = await _create_reserva_in_db(
        db_session, test_tenant.id, produto.id, Decimal("5.000")
    )
    estoque.reserved_quantity = Decimal("5.000")
    await db_session.commit()

    response = await client.post(
        f"/api/v1/estoque/reservas/{reserva.id}/cancelar",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CANCELADA"
    assert data["released_at"] is not None


@pytest.mark.asyncio
async def test_confirm_already_confirmed_reserva(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto Q", "SKU-Q", categoria.id
    )
    reserva = await _create_reserva_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        Decimal("5.000"),
        StatusReserva.CONFIRMADA,
    )
    await db_session.commit()

    response = await client.post(
        f"/api/v1/estoque/reservas/{reserva.id}/confirmar",
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_reservas(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Produto R", "SKU-R", categoria.id
    )
    await _create_reserva_in_db(
        db_session, test_tenant.id, produto.id, Decimal("5.000"), idempotency_key="r1"
    )
    await _create_reserva_in_db(
        db_session, test_tenant.id, produto.id, Decimal("3.000"), idempotency_key="r2"
    )
    await db_session.commit()

    response = await client.get(
        "/api/v1/estoque/reservas/list",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


# --- SALDO ---


@pytest.mark.asyncio
async def test_list_estoque_saldos(
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
    await _create_estoque_in_db(db_session, test_tenant.id, p1.id)
    await _create_estoque_in_db(db_session, test_tenant.id, p2.id)
    await db_session.commit()

    response = await client.get(
        "/api/v1/estoque",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_get_single_saldo(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "Prod Single", "SKU-S", categoria.id
    )
    await _create_estoque_in_db(
        db_session, test_tenant.id, produto.id, quantity=Decimal("42.000")
    )
    await db_session.commit()

    response = await client.get(
        f"/api/v1/estoque/{produto.id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == "42.000"
    assert data["produto_id"] == produto.id


@pytest.mark.asyncio
async def test_get_nonexistent_saldo(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    response = await client.get(
        "/api/v1/estoque/99999",
        headers=admin_headers,
    )
    assert response.status_code == 404


# --- MULTI-TENANCY ---


@pytest.mark.asyncio
async def test_cannot_access_other_tenant_estoque(
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
    await _create_estoque_in_db(db_session, test_tenant.id, produto.id)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/estoque/{produto.id}",
        headers=other_tenant_headers,
    )
    assert response.status_code == 404


# --- RBAC ---


@pytest.mark.asyncio
async def test_read_only_user_can_list(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    read_only_headers: dict[str, str],
) -> None:
    response = await client.get(
        "/api/v1/estoque",
        headers=read_only_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_read_only_user_cannot_create_movimentacao(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
) -> None:
    ro_role = await _create_role_with_perms(
        db_session, test_tenant.id, "inv_readonly", ["estoque.ler"]
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
        "/api/v1/estoque/movimentacoes",
        json={
            "produto_id": produto.id,
            "tipo_movimentacao": "ENTRADA",
            "quantity": "10.000",
            "idempotency_key": "ro-movimentacao",
        },
        headers=ro_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_cannot_access(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/estoque")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_movimentacao_on_inactive_produto_allowed(
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
    await _create_estoque_in_db(db_session, test_tenant.id, produto.id)
    await db_session.commit()

    response = await client.post(
        "/api/v1/estoque/movimentacoes",
        json={
            "produto_id": produto.id,
            "tipo_movimentacao": "ENTRADA",
            "quantity": "5.000",
            "idempotency_key": "inactive-in",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_ajuste_must_be_positive(
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
        "/api/v1/estoque/movimentacoes",
        json={
            "produto_id": produto.id,
            "tipo_movimentacao": "AJUSTE",
            "quantity": "0.000",
            "idempotency_key": "adj-zero",
        },
        headers=admin_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_tipo_movimentacao(
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
        "/api/v1/estoque/movimentacoes",
        json={
            "produto_id": produto.id,
            "tipo_movimentacao": "INVALID",
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
        await _create_movimentacao_in_db(
            db_session,
            test_tenant.id,
            produto.id,
            "ENTRADA",
            Decimal("1.000"),
            f"pag-key-{i}",
        )
    await db_session.commit()

    response = await client.get(
        "/api/v1/estoque/movimentacoes/list?page=1&page_size=2",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2


# --- AUDITORIA CRITICA ---


@pytest.mark.asyncio
async def test_idempotent_reserva_returns_same(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "IdemRes", "SKU-IR", categoria.id
    )
    await _create_estoque_in_db(
        db_session, test_tenant.id, produto.id, quantity=Decimal("50.000")
    )
    await db_session.commit()

    response1 = await client.post(
        "/api/v1/estoque/reservas",
        json={
            "produto_id": produto.id,
            "quantity": "10.000",
            "idempotency_key": "res-idempotent-1",
        },
        headers=admin_headers,
    )
    assert response1.status_code == 201
    assert response1.json()["status"] == "ATIVA"

    response2 = await client.post(
        "/api/v1/estoque/reservas",
        json={
            "produto_id": produto.id,
            "quantity": "20.000",
            "idempotency_key": "res-idempotent-1",
        },
        headers=admin_headers,
    )
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_released_reserva_cannot_be_confirmed(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "RelCf", "SKU-RC", categoria.id
    )
    reserva = await _create_reserva_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        Decimal("5.000"),
        StatusReserva.LIBERADA,
    )
    await db_session.commit()

    response = await client.post(
        f"/api/v1/estoque/reservas/{reserva.id}/confirmar",
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_cancelled_reserva_cannot_be_confirmed(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "CanCf", "SKU-CC", categoria.id
    )
    reserva = await _create_reserva_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        Decimal("5.000"),
        StatusReserva.CANCELADA,
    )
    await db_session.commit()

    response = await client.post(
        f"/api/v1/estoque/reservas/{reserva.id}/confirmar",
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_confirmed_reserva_cannot_be_released(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "CfRel", "SKU-CR", categoria.id
    )
    reserva = await _create_reserva_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        Decimal("5.000"),
        StatusReserva.CONFIRMADA,
    )
    await db_session.commit()

    response = await client.post(
        f"/api/v1/estoque/reservas/{reserva.id}/liberar",
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_saida_at_boundary_exactly_available(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "BoundOut", "SKU-BO", categoria.id
    )
    await _create_estoque_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        quantity=Decimal("100.000"),
        reserved_quantity=Decimal("30.000"),
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/estoque/movimentacoes",
        json={
            "produto_id": produto.id,
            "tipo_movimentacao": "SAIDA",
            "quantity": "70.000",
            "idempotency_key": "out-boundary-ok",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_saida_one_over_boundary_fails(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    admin_headers: dict[str, str],
) -> None:
    categoria = await _create_categoria_in_db(db_session, test_tenant.id, "Cat")
    produto = await _create_produto_in_db(
        db_session, test_tenant.id, "BoundOutFail", "SKU-BOF", categoria.id
    )
    await _create_estoque_in_db(
        db_session,
        test_tenant.id,
        produto.id,
        quantity=Decimal("100.000"),
        reserved_quantity=Decimal("30.000"),
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/estoque/movimentacoes",
        json={
            "produto_id": produto.id,
            "tipo_movimentacao": "SAIDA",
            "quantity": "71.000",
            "idempotency_key": "out-boundary-fail",
        },
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_cross_tenant_cannot_create_movimentacao_on_other_tenant_produto(
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
        "/api/v1/estoque/movimentacoes",
        json={
            "produto_id": produto.id,
            "tipo_movimentacao": "ENTRADA",
            "quantity": "10.000",
            "idempotency_key": "cross-tenant-movimentacao",
        },
        headers=other_tenant_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cross_tenant_cannot_create_reserva_on_other_tenant_produto(
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
        "/api/v1/estoque/reservas",
        json={
            "produto_id": produto.id,
            "quantity": "5.000",
            "idempotency_key": "cross-tenant-reserva",
        },
        headers=other_tenant_headers,
    )
    assert response.status_code == 404
