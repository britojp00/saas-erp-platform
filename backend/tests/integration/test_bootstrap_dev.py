import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import ALL_PERMISSIONS, PROFILES, READ_PERMISSIONS
from app.core.security import create_access_token, verify_password
from app.db.models.empresa import Empresa
from app.db.models.permission import Permission
from app.db.models.role import Role
from app.db.models.role_permission import RolePermission
from app.db.models.user import User
from app.db.models.user_role import UserRole
from scripts.bootstrap_dev import (
    BootstrapConfigError,
    bootstrap,
    rename_legacy_permissions,
)

ADMIN_EMAIL = "admin@dev.local"
ADMIN_PASSWORD = "senha-desenvolvimento-2026"


async def _bootstrap_dev(session: AsyncSession) -> int:
    return await bootstrap(
        session,
        empresa_slug="dev",
        empresa_name="Development",
        admin_email=ADMIN_EMAIL,
        admin_password=ADMIN_PASSWORD,
        admin_full_name="Admin Development",
    )


async def _count(session: AsyncSession, model) -> int:
    stmt = select(func.count()).select_from(model)
    return (await session.execute(stmt)).scalar_one()


async def _permission_names(session: AsyncSession, empresa_id: int) -> list[str]:
    stmt = (
        select(Permission.name)
        .where(Permission.empresa_id == empresa_id)
        .order_by(Permission.name)
    )
    return list((await session.execute(stmt)).scalars().all())


@pytest.mark.asyncio
async def test_bootstrap_cria_base_e_primeiro_admin(
    db_session: AsyncSession,
) -> None:
    await _bootstrap_dev(db_session)

    empresa = (
        await db_session.execute(select(Empresa).where(Empresa.slug == "dev"))
    ).scalar_one()

    assert await _count(db_session, Permission) == len(ALL_PERMISSIONS)
    assert await _count(db_session, Role) == len(PROFILES)

    admin_role = (
        await db_session.execute(
            select(Role).where(Role.empresa_id == empresa.id, Role.name == "admin")
        )
    ).scalar_one()
    viewer_role = (
        await db_session.execute(
            select(Role).where(Role.empresa_id == empresa.id, Role.name == "viewer")
        )
    ).scalar_one()

    admin_permissions = set(await _permission_names(db_session, empresa.id))
    assert admin_permissions == set(ALL_PERMISSIONS)

    viewer_count = (
        await db_session.execute(
            select(func.count())
            .select_from(RolePermission)
            .where(RolePermission.role_id == viewer_role.id)
        )
    ).scalar_one()
    assert viewer_count == len(READ_PERMISSIONS)

    admin_permissions_count = (
        await db_session.execute(
            select(func.count())
            .select_from(RolePermission)
            .where(RolePermission.role_id == admin_role.id)
        )
    ).scalar_one()
    assert admin_permissions_count == len(ALL_PERMISSIONS)

    user = (
        await db_session.execute(select(User).where(User.email == ADMIN_EMAIL))
    ).scalar_one()
    assert user.empresa_id == empresa.id
    assert user.is_active is True
    assert verify_password(ADMIN_PASSWORD, user.password_hash) is True
    assert "senha-desenvolvimento-2026" not in user.password_hash

    bound_role = (
        await db_session.execute(
            select(UserRole.role_id).where(UserRole.user_id == user.id)
        )
    ).scalar_one()
    assert bound_role == admin_role.id


@pytest.mark.asyncio
async def test_bootstrap_e_idempotente(db_session: AsyncSession) -> None:
    await _bootstrap_dev(db_session)
    empresas = await _count(db_session, Empresa)
    users = await _count(db_session, User)
    permissions = await _count(db_session, Permission)
    roles = await _count(db_session, Role)
    bindings = await _count(db_session, RolePermission)

    renamed = await _bootstrap_dev(db_session)

    assert renamed == 0
    assert await _count(db_session, Empresa) == empresas
    assert await _count(db_session, User) == users
    assert await _count(db_session, Permission) == permissions
    assert await _count(db_session, Role) == roles
    assert await _count(db_session, RolePermission) == bindings


@pytest.mark.asyncio
async def test_bootstrap_nao_sobrescreve_usuario_existente(
    db_session: AsyncSession,
) -> None:
    await _bootstrap_dev(db_session)

    await bootstrap(
        db_session,
        empresa_slug="dev",
        empresa_name="Development",
        admin_email="outro@dev.local",
        admin_password="outra-senha-dev-2026",
        admin_full_name="Outro Admin",
    )

    assert await _count(db_session, User) == 1
    user = (
        await db_session.execute(select(User).where(User.email == ADMIN_EMAIL))
    ).scalar_one()
    assert verify_password(ADMIN_PASSWORD, user.password_hash) is True


@pytest.mark.asyncio
async def test_bootstrap_fala_quando_nao_ha_credenciais(
    db_session: AsyncSession,
) -> None:
    with pytest.raises(BootstrapConfigError):
        await bootstrap(
            db_session,
            empresa_slug="dev",
            empresa_name="Development",
            admin_email=None,
            admin_password=None,
            admin_full_name="Admin Development",
        )

    await db_session.rollback()
    assert await _count(db_session, Empresa) == 0
    assert await _count(db_session, User) == 0


@pytest.mark.asyncio
async def test_renomeacao_legada_preserva_vinculos(
    db_session: AsyncSession,
) -> None:
    empresa_legacy = Empresa(
        name="Empresa Legacy",
        slug="legacy",
        is_active=True,
    )
    empresa_mixed = Empresa(
        name="Empresa Mixed",
        slug="mixed",
        is_active=True,
    )
    db_session.add_all([empresa_legacy, empresa_mixed])
    await db_session.flush()

    legacy_permission = Permission(empresa_id=empresa_legacy.id, name="role.read")
    db_session.add(legacy_permission)
    await db_session.flush()

    legacy_role = Role(empresa_id=empresa_legacy.id, name="auditor")
    db_session.add(legacy_role)
    await db_session.flush()
    db_session.add(
        RolePermission(
            empresa_id=empresa_legacy.id,
            role_id=legacy_role.id,
            permission_id=legacy_permission.id,
        )
    )

    mixed_legacy = Permission(empresa_id=empresa_mixed.id, name="role.read")
    mixed_current = Permission(empresa_id=empresa_mixed.id, name="role.ler")
    db_session.add_all([mixed_legacy, mixed_current])
    await db_session.flush()

    legacy_binding_role = Role(empresa_id=empresa_mixed.id, name="antigo")
    current_binding_role = Role(empresa_id=empresa_mixed.id, name="atual")
    db_session.add_all([legacy_binding_role, current_binding_role])
    await db_session.flush()
    db_session.add_all(
        [
            RolePermission(
                empresa_id=empresa_mixed.id,
                role_id=legacy_binding_role.id,
                permission_id=mixed_legacy.id,
            ),
            RolePermission(
                empresa_id=empresa_mixed.id,
                role_id=current_binding_role.id,
                permission_id=mixed_current.id,
            ),
        ]
    )
    await db_session.flush()

    renamed = await rename_legacy_permissions(db_session)
    await db_session.commit()

    assert renamed == 2
    assert await _count(db_session, Permission) == 2

    legacy_names = await _permission_names(db_session, empresa_legacy.id)
    assert legacy_names == ["role.ler"]

    mixed_names = await _permission_names(db_session, empresa_mixed.id)
    assert mixed_names == ["role.ler"]

    legacy_binding = (
        await db_session.execute(
            select(RolePermission.permission_id).where(
                RolePermission.empresa_id == empresa_legacy.id,
                RolePermission.role_id == legacy_role.id,
            )
        )
    ).scalar_one()
    assert legacy_binding == legacy_permission.id

    mixed_bindings = list(
        (
            await db_session.execute(
                select(RolePermission).where(
                    RolePermission.empresa_id == empresa_mixed.id
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(mixed_bindings) == 2
    permission_ids = {binding.permission_id for binding in mixed_bindings}
    current_id = (
        await db_session.execute(
            select(Permission.id).where(
                Permission.empresa_id == empresa_mixed.id,
                Permission.name == "role.ler",
            )
        )
    ).scalar_one()
    assert permission_ids == {current_id}


@pytest.mark.asyncio
async def test_api_de_auditoria_funciona_com_permissao_ptbr(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await _bootstrap_dev(db_session)

    admin = (
        await db_session.execute(select(User).where(User.email == ADMIN_EMAIL))
    ).scalar_one()
    empresa = (
        await db_session.execute(select(Empresa).where(Empresa.slug == "dev"))
    ).scalar_one()

    token = create_access_token(
        data={"sub": str(admin.id), "empresa_id": str(empresa.id)}
    )
    headers = {"Authorization": f"Bearer {token}"}

    audit_response = await client.get("/api/v1/audit-logs", headers=headers)
    assert audit_response.status_code == 200

    roles_response = await client.get("/api/v1/auth/roles", headers=headers)
    assert roles_response.status_code == 200
