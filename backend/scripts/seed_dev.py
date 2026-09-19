import asyncio
import os
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.models.permission import Permission
from app.db.models.role import Role
from app.db.models.role_permission import RolePermission
from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.db.models.user_role import UserRole

engine = create_async_engine(settings.database_url, echo=False)
session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

SEED_TENANT_SLUG = "demo"
SEED_USER_EMAIL = "admin@demo.com"
DEFAULT_DEV_PASSWORD = "admin123"

ALL_PERMISSIONS = [
    "customer.read",
    "customer.create",
    "customer.update",
    "customer.delete",
    "product.read",
    "product.create",
    "product.update",
    "product.delete",
    "category.read",
    "category.create",
    "category.update",
    "category.delete",
    "order.read",
    "order.create",
    "order.update",
    "order.cancel",
    "inventory.read",
    "inventory.update",
    "user.read",
    "user.create",
    "user.update",
    "user.delete",
    "role.read",
    "role.create",
    "role.update",
    "role.delete",
    "permission.read",
]

MANAGER_EXCLUDED = {"user.delete", "role.delete", "permission.read"}

READ_PERMISSIONS = {p for p in ALL_PERMISSIONS if p.endswith(".read")}


async def _get_or_create_permission(
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
    print(f"  Permission '{name}' criada (id={perm.id}).")
    return perm


async def _get_or_create_role(
    session: AsyncSession,
    tenant_id: int,
    name: str,
    description: str,
) -> Role:
    stmt = select(Role).where(
        Role.tenant_id == tenant_id,
        Role.name == name,
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        print(f"  Role '{name}' já existe (id={existing.id}).")
        return existing
    role = Role(tenant_id=tenant_id, name=name, description=description)
    session.add(role)
    await session.flush()
    print(f"  Role '{name}' criada (id={role.id}).")
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


async def seed() -> None:
    dev_password = os.environ.get("SEED_PASSWORD", DEFAULT_DEV_PASSWORD)

    async with session_factory() as session:
        stmt = select(Tenant).where(Tenant.slug == SEED_TENANT_SLUG)
        result = await session.execute(stmt)
        existing_tenant = result.scalar_one_or_none()

        if existing_tenant:
            tenant = existing_tenant
            print(f"Tenant '{SEED_TENANT_SLUG}' já existe (id={tenant.id}).")
        else:
            tenant = Tenant(
                name="Demo Company",
                slug=SEED_TENANT_SLUG,
                is_active=True,
            )
            session.add(tenant)
            await session.flush()
            print(f"Tenant '{SEED_TENANT_SLUG}' criado (id={tenant.id}).")

        stmt = select(User).where(
            User.email == SEED_USER_EMAIL,
            User.tenant_id == tenant.id,
        )
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            user = existing_user
            print(f"Usuário '{SEED_USER_EMAIL}' já existe (id={user.id}).")
        else:
            user = User(
                tenant_id=tenant.id,
                email=SEED_USER_EMAIL,
                password_hash=get_password_hash(dev_password),
                full_name="Admin User",
                is_active=True,
            )
            session.add(user)
            await session.flush()
            print(f"Usuário '{SEED_USER_EMAIL}' criado (id={user.id}).")

        print("\n--- Criando permissions ---")
        perm_map: dict[str, Permission] = {}
        for name in ALL_PERMISSIONS:
            perm = await _get_or_create_permission(session, tenant.id, name)
            perm_map[name] = perm

        print("\n--- Criando roles ---")
        admin_role = await _get_or_create_role(
            session, tenant.id, "admin", "Administrador do sistema"
        )
        manager_role = await _get_or_create_role(
            session, tenant.id, "manager", "Gerente"
        )
        viewer_role = await _get_or_create_role(
            session, tenant.id, "viewer", "Visualizador"
        )

        print("\n--- Atribuindo permissions aos roles ---")
        for name, perm in perm_map.items():
            await _assign_permission(session, tenant.id, admin_role.id, perm.id)

        manager_perms = {p for p in ALL_PERMISSIONS if p not in MANAGER_EXCLUDED}
        for name in manager_perms:
            await _assign_permission(
                session, tenant.id, manager_role.id, perm_map[name].id
            )

        for name in READ_PERMISSIONS:
            await _assign_permission(
                session, tenant.id, viewer_role.id, perm_map[name].id
            )

        print("\n--- Atribuindo role admin ao usuário ---")
        await _assign_role_to_user(session, tenant.id, user.id, admin_role.id)

        await session.commit()
        print("\nSeed concluído com sucesso.")


if __name__ == "__main__":
    asyncio.run(seed())
