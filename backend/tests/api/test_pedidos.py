from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cliente import Cliente
from app.db.models.estoque import Estoque
from app.db.models.pedido import Pedido
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


async def _create_cliente_in_db(
    session: AsyncSession,
    tenant_id: int,
    name: str,
) -> Cliente:
    cliente = Cliente(
        tenant_id=tenant_id,
        name=name,
    )
    session.add(cliente)
    await session.flush()
    return cliente


async def _create_produto_in_db(
    session: AsyncClient,
    tenant_id: int,
    name: str,
    price: Decimal = Decimal("10.00"),
    is_active: bool = True,
) -> Produto:
    produto = Produto(
        tenant_id=tenant_id,
        sku=f"SKU-{name.upper().replace(' ', '-')}",
        name=name,
        price=price,
        is_active=is_active,
    )
    session = produto  # type: ignore[assignment]
    session = None  # noqa: F841  # will be passed as parameter
    return produto


async def _create_produto(
    session: AsyncSession,
    tenant_id: int,
    name: str,
    price: Decimal = Decimal("10.00"),
    is_active: bool = True,
) -> Produto:
    produto = Produto(
        tenant_id=tenant_id,
        sku=f"SKU-{name.upper().replace(' ', '-')}",
        name=name,
        price=price,
        is_active=is_active,
    )
    session.add(produto)
    await session.flush()
    return produto


async def _create_estoque(
    session: AsyncSession,
    tenant_id: int,
    produto_id: int,
    quantity: Decimal = Decimal("100.000"),
) -> Estoque:
    estoque = Estoque(
        tenant_id=tenant_id,
        produto_id=produto_id,
        quantity=quantity,
    )
    session.add(estoque)
    await session.flush()
    return estoque


@pytest.fixture
async def cliente(db_session: AsyncSession, test_tenant: Tenant) -> Cliente:
    return await _create_cliente_in_db(db_session, test_tenant.id, "Cliente Teste")


@pytest.fixture
async def produto(db_session: AsyncSession, test_tenant: Tenant) -> Produto:
    return await _create_produto(db_session, test_tenant.id, "Produto Teste")


@pytest.fixture
async def produto_b(db_session: AsyncSession, test_tenant: Tenant) -> Produto:
    return await _create_produto(
        db_session, test_tenant.id, "Produto B", price=Decimal("25.00")
    )


@pytest.fixture
async def estoque(
    db_session: AsyncSession, test_tenant: Tenant, produto: Produto
) -> Estoque:
    return await _create_estoque(db_session, test_tenant.id, produto.id)


@pytest.fixture
async def estoque_b(
    db_session: AsyncSession, test_tenant: Tenant, produto_b: Produto
) -> Estoque:
    return await _create_estoque(db_session, test_tenant.id, produto_b.id)


@pytest.fixture
async def pedido_com_itens(
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    cliente: Cliente,
    produto: Produto,
    estoque: Estoque,
) -> Pedido:
    role = await _create_role_with_perms(
        db_session,
        test_tenant.id,
        "pedido_admin",
        [
            "pedido.ler",
            "pedido.criar",
            "pedido.atualizar",
            "pedido.cancelar",
        ],
    )
    await _assign_role_to_user(db_session, test_tenant.id, test_user.id, role.id)
    await db_session.commit()
    return cliente  # type: ignore[return-value]


class TestPedidoCriacao:
    async def test_criar_pedido_com_itens(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_creator",
            ["pedido.ler", "pedido.criar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        response = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 2}],
            },
            headers=authenticated_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "RASCUNHO"
        assert data["cliente_id"] == cliente.id
        assert len(data["itens"]) == 1
        assert data["itens"][0]["produto_id"] == produto.id
        assert data["itens"][0]["quantity"] == 2.0
        assert data["itens"][0]["unit_price"] == float(produto.price)
        assert data["total_amount"] == float(produto.price) * 2
        assert isinstance(data["numero_pedido"], int)

    async def test_criar_pedido_multiplos_itens(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        produto_b: Produto,
        estoque: Estoque,
        estoque_b: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_creator",
            ["pedido.ler", "pedido.criar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        response = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [
                    {"produto_id": produto.id, "quantity": 2},
                    {"produto_id": produto_b.id, "quantity": 1},
                ],
            },
            headers=authenticated_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["itens"]) == 2
        expected_total = float(produto.price) * 2 + float(produto_b.price) * 1
        assert float(Decimal(str(data["total_amount"]))) == expected_total

    async def test_criar_pedido_sem_itens_falha(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_creator",
            ["pedido.ler", "pedido.criar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        response = await client.post(
            "/api/v1/pedidos",
            json={"cliente_id": cliente.id, "itens": []},
            headers=authenticated_headers,
        )
        assert response.status_code == 422

    async def test_criar_pedido_cliente_inexistente_falha(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_creator",
            ["pedido.ler", "pedido.criar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        response = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": 99999,
                "itens": [{"produto_id": produto.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        assert response.status_code == 409

    async def test_criar_pedido_produto_inexistente_falha(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_creator",
            ["pedido.ler", "pedido.criar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        response = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": 99999, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        assert response.status_code == 409

    async def test_criar_pedido_produto_duplicado_falha(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_creator",
            ["pedido.ler", "pedido.criar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        response = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [
                    {"produto_id": produto.id, "quantity": 1},
                    {"produto_id": produto.id, "quantity": 2},
                ],
            },
            headers=authenticated_headers,
        )
        assert response.status_code == 409

    async def test_criar_pedido_com_preco_unitario_customizado(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_creator",
            ["pedido.ler", "pedido.criar"],
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
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [
                    {
                        "produto_id": produto.id,
                        "quantity": 3,
                        "unit_price": str(custom_price),
                    }
                ],
            },
            headers=authenticated_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["itens"][0]["unit_price"] == float(custom_price)
        assert abs(Decimal(str(data["total_amount"])) - custom_price * 3) < Decimal(
            "0.01"
        )


class TestPedidoNumero:
    async def test_numero_pedido_sequencial(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_creator",
            ["pedido.ler", "pedido.criar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        resp1 = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        assert resp1.status_code == 201
        num1 = resp1.json()["numero_pedido"]

        resp2 = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        assert resp2.status_code == 201
        num2 = resp2.json()["numero_pedido"]

        assert num2 == num1 + 1


class TestPedidoListaEDetalhe:
    async def test_listar_pedidos(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_list",
            ["pedido.ler", "pedido.criar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )

        response = await client.get(
            "/api/v1/pedidos",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["itens"]) >= 1

    async def test_listar_pedidos_filtro_por_status(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_list",
            ["pedido.ler", "pedido.criar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )

        response = await client.get(
            "/api/v1/pedidos",
            params={"status": "RASCUNHO"},
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        for item in response.json()["itens"]:
            assert item["status"] == "RASCUNHO"

    async def test_obter_detalhe_pedido(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_detail",
            ["pedido.ler", "pedido.criar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]

        response = await client.get(
            f"/api/v1/pedidos/{pedido_id}",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == pedido_id
        assert len(data["itens"]) == 1

    async def test_obter_pedido_inexistente_falha(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_detail",
            ["pedido.ler"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        response = await client.get(
            "/api/v1/pedidos/99999",
            headers=authenticated_headers,
        )
        assert response.status_code == 404


class TestPedidoAtualizacao:
    async def test_atualizar_pedido_cliente(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_update",
            ["pedido.ler", "pedido.criar", "pedido.atualizar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]

        new_cliente = await _create_cliente_in_db(
            db_session, test_tenant.id, "Novo Cliente"
        )
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/pedidos/{pedido_id}",
            json={"cliente_id": new_cliente.id},
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert response.json()["cliente_id"] == new_cliente.id

    async def test_atualizar_pedido_nao_rascunho_falha(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_update",
            ["pedido.ler", "pedido.criar", "pedido.atualizar", "pedido.cancelar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/pedidos/{pedido_id}/confirmar",
            headers=authenticated_headers,
        )

        response = await client.patch(
            f"/api/v1/pedidos/{pedido_id}",
            json={"notes": "Should fail"},
            headers=authenticated_headers,
        )
        assert response.status_code == 409


class TestPedidoItens:
    async def test_adicionar_item_ao_pedido(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        produto_b: Produto,
        estoque: Estoque,
        estoque_b: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_items",
            ["pedido.ler", "pedido.criar", "pedido.atualizar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/pedidos/{pedido_id}/itens",
            json={"produto_id": produto_b.id, "quantity": 3},
            headers=authenticated_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["produto_id"] == produto_b.id
        assert data["quantity"] == 3.0

        detail_resp = await client.get(
            f"/api/v1/pedidos/{pedido_id}",
            headers=authenticated_headers,
        )
        assert detail_resp.status_code == 200
        assert len(detail_resp.json()["itens"]) == 2

    async def test_adicionar_produto_duplicado_ao_pedido_falha(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_items",
            ["pedido.ler", "pedido.criar", "pedido.atualizar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/pedidos/{pedido_id}/itens",
            json={"produto_id": produto.id, "quantity": 2},
            headers=authenticated_headers,
        )
        assert response.status_code == 409

    async def test_atualizar_quantidade_item(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_items",
            ["pedido.ler", "pedido.criar", "pedido.atualizar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]
        item_id = create_resp.json()["itens"][0]["id"]

        response = await client.patch(
            f"/api/v1/pedidos/{pedido_id}/itens/{item_id}",
            json={"quantity": 5},
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert response.json()["quantity"] == 5.0

        detail_resp = await client.get(
            f"/api/v1/pedidos/{pedido_id}",
            headers=authenticated_headers,
        )
        assert (
            float(Decimal(str(detail_resp.json()["total_amount"])))
            == float(produto.price) * 5
        )

    async def test_remover_item_do_pedido(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        produto_b: Produto,
        estoque: Estoque,
        estoque_b: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_items",
            ["pedido.ler", "pedido.criar", "pedido.atualizar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [
                    {"produto_id": produto.id, "quantity": 1},
                    {"produto_id": produto_b.id, "quantity": 2},
                ],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]
        item_to_remove = create_resp.json()["itens"][1]["id"]

        response = await client.delete(
            f"/api/v1/pedidos/{pedido_id}/itens/{item_to_remove}",
            headers=authenticated_headers,
        )
        assert response.status_code == 204

        detail_resp = await client.get(
            f"/api/v1/pedidos/{pedido_id}",
            headers=authenticated_headers,
        )
        assert len(detail_resp.json()["itens"]) == 1

    async def test_remover_ultimo_item_falha(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_items",
            ["pedido.ler", "pedido.criar", "pedido.atualizar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]
        item_id = create_resp.json()["itens"][0]["id"]

        response = await client.delete(
            f"/api/v1/pedidos/{pedido_id}/itens/{item_id}",
            headers=authenticated_headers,
        )
        assert response.status_code == 409

    async def test_adicionar_item_em_nao_rascunho_falha(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        produto_b: Produto,
        estoque: Estoque,
        estoque_b: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_items",
            ["pedido.ler", "pedido.criar", "pedido.atualizar", "pedido.cancelar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/pedidos/{pedido_id}/confirmar",
            headers=authenticated_headers,
        )

        response = await client.post(
            f"/api/v1/pedidos/{pedido_id}/itens",
            json={"produto_id": produto_b.id, "quantity": 1},
            headers=authenticated_headers,
        )
        assert response.status_code == 409


class TestPedidoMaquinaDeEstados:
    async def test_confirmar_pedido(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_confirm",
            [
                "pedido.ler",
                "pedido.criar",
                "pedido.atualizar",
                "estoque.ler",
                "estoque.atualizar",
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
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 5}],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/pedidos/{pedido_id}/confirmar",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "CONFIRMADO"

        inv_resp = await client.get(
            f"/api/v1/estoque/{produto.id}",
            headers=authenticated_headers,
        )
        assert inv_resp.status_code == 200
        assert float(inv_resp.json()["reserved_quantity"]) == 5.0

    async def test_concluir_pedido(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_complete",
            ["pedido.ler", "pedido.criar", "pedido.atualizar", "estoque.ler"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 5}],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/pedidos/{pedido_id}/confirmar",
            headers=authenticated_headers,
        )

        response = await client.post(
            f"/api/v1/pedidos/{pedido_id}/concluir",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "CONCLUIDO"

        inv_resp = await client.get(
            f"/api/v1/estoque/{produto.id}",
            headers=authenticated_headers,
        )
        assert inv_resp.status_code == 200
        assert float(inv_resp.json()["quantity"]) == 95.0
        assert float(inv_resp.json()["reserved_quantity"]) == 0.0

    async def test_cancelar_pedido_rascunho(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_cancel",
            ["pedido.ler", "pedido.criar", "pedido.atualizar", "pedido.cancelar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 5}],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/pedidos/{pedido_id}/cancelar",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "CANCELADO"

    async def test_cancelar_pedido_confirmado_libera_reservas(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_cancel",
            [
                "pedido.ler",
                "pedido.criar",
                "pedido.atualizar",
                "pedido.cancelar",
                "estoque.ler",
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
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 5}],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/pedidos/{pedido_id}/confirmar",
            headers=authenticated_headers,
        )

        response = await client.post(
            f"/api/v1/pedidos/{pedido_id}/cancelar",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "CANCELADO"

        inv_resp = await client.get(
            f"/api/v1/estoque/{produto.id}",
            headers=authenticated_headers,
        )
        assert inv_resp.status_code == 200
        assert float(inv_resp.json()["reserved_quantity"]) == 0.0

    async def test_concluir_sem_confirmar_falha(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_complete",
            ["pedido.ler", "pedido.criar", "pedido.atualizar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/pedidos/{pedido_id}/concluir",
            headers=authenticated_headers,
        )
        assert response.status_code == 409

    async def test_confirmar_pedido_concluido_falha(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_terminal",
            ["pedido.ler", "pedido.criar", "pedido.atualizar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/pedidos/{pedido_id}/confirmar",
            headers=authenticated_headers,
        )
        await client.post(
            f"/api/v1/pedidos/{pedido_id}/concluir",
            headers=authenticated_headers,
        )

        response = await client.post(
            f"/api/v1/pedidos/{pedido_id}/confirmar",
            headers=authenticated_headers,
        )
        assert response.status_code == 409

    async def test_confirmar_pedido_cancelado_falha(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_terminal",
            ["pedido.ler", "pedido.criar", "pedido.atualizar", "pedido.cancelar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 1}],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/pedidos/{pedido_id}/cancelar",
            headers=authenticated_headers,
        )

        response = await client.post(
            f"/api/v1/pedidos/{pedido_id}/confirmar",
            headers=authenticated_headers,
        )
        assert response.status_code == 409


class TestPedidoRBAC:
    async def test_criar_pedido_sem_permissao_falha(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        authenticated_headers: dict,
    ) -> None:
        response = await client.post(
            "/api/v1/pedidos",
            json={"cliente_id": 1, "itens": [{"produto_id": 1, "quantity": 1}]},
            headers=authenticated_headers,
        )
        assert response.status_code == 403

    async def test_listar_pedidos_sem_permissao_falha(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        authenticated_headers: dict,
    ) -> None:
        response = await client.get(
            "/api/v1/pedidos",
            headers=authenticated_headers,
        )
        assert response.status_code == 403

    async def test_obter_pedido_sem_permissao_falha(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        authenticated_headers: dict,
    ) -> None:
        response = await client.get(
            "/api/v1/pedidos/1",
            headers=authenticated_headers,
        )
        assert response.status_code == 403


class TestPedidoMultiTenancy:
    async def test_nao_acessa_pedido_de_outro_tenant(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        from app.core.security import create_access_token

        other_tenant = Tenant(name="Outro Tenant", slug="outro-tenant")
        db_session.add(other_tenant)
        await db_session.flush()

        other_cliente = Cliente(tenant_id=other_tenant.id, name="Outro Cliente")
        db_session.add(other_cliente)
        await db_session.flush()

        other_produto = Produto(
            tenant_id=other_tenant.id,
            sku="SKU-OUTRO",
            name="Outro Produto",
            price=Decimal("50.00"),
        )
        db_session.add(other_produto)
        await db_session.flush()

        other_estoque = Estoque(
            tenant_id=other_tenant.id,
            produto_id=other_produto.id,
            quantity=Decimal("100.000"),
        )
        db_session.add(other_estoque)
        await db_session.flush()

        other_perm = Permission(tenant_id=other_tenant.id, name="pedido.ler")
        db_session.add(other_perm)
        await db_session.flush()

        other_perm_create = Permission(tenant_id=other_tenant.id, name="pedido.criar")
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
            "/api/v1/pedidos",
            json={
                "cliente_id": other_cliente.id,
                "itens": [{"produto_id": other_produto.id, "quantity": 1}],
            },
            headers=other_headers,
        )
        assert create_resp.status_code == 201
        other_pedido_id = create_resp.json()["id"]

        response = await client.get(
            f"/api/v1/pedidos/{other_pedido_id}",
            headers=authenticated_headers,
        )
        assert response.status_code in (403, 404)


class TestPedidoEstoqueIntegracao:
    async def test_estoque_insuficiente_falha(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        authenticated_headers: dict,
        cliente: Cliente,
        produto: Produto,
        estoque: Estoque,
    ) -> None:
        role = await _create_role_with_perms(
            db_session,
            test_tenant.id,
            "pedido_insufficient",
            ["pedido.ler", "pedido.criar", "pedido.atualizar"],
        )
        await _assign_role_to_user(
            db_session,
            test_tenant.id,
            (await _get_user(db_session, test_tenant.id)).id,
            role.id,
        )
        await db_session.commit()

        create_resp = await client.post(
            "/api/v1/pedidos",
            json={
                "cliente_id": cliente.id,
                "itens": [{"produto_id": produto.id, "quantity": 200}],
            },
            headers=authenticated_headers,
        )
        pedido_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/pedidos/{pedido_id}/confirmar",
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
