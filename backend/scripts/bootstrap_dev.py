import asyncio
import os
import sys

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.core.permissions import (
    ALL_PERMISSIONS,
    LEGACY_RENAMES,
    MANAGER_EXCLUDED,
    PROFILES,
    READ_PERMISSIONS,
)
from app.core.security import get_password_hash
from app.db.models.empresa import Empresa
from app.db.models.permission import Permission
from app.db.models.role import Role
from app.db.models.role_permission import RolePermission
from app.db.models.user import User
from app.db.models.user_role import UserRole

ENV_EMPRESA_SLUG = "BOOTSTRAP_DEV_EMPRESA_SLUG"
ENV_EMPRESA_NAME = "BOOTSTRAP_DEV_EMPRESA_NAME"
ENV_ADMIN_EMAIL = "BOOTSTRAP_DEV_ADMIN_EMAIL"
ENV_ADMIN_PASSWORD = "BOOTSTRAP_DEV_ADMIN_PASSWORD"
ENV_ADMIN_NAME = "BOOTSTRAP_DEV_ADMIN_NAME"


class BootstrapConfigError(Exception):
    pass


async def _move_bindings(
    session: AsyncSession,
    origin: Permission,
    target: Permission,
) -> None:
    stmt = select(RolePermission).where(
        RolePermission.empresa_id == origin.empresa_id,
        RolePermission.permission_id == origin.id,
    )
    bindings = (await session.execute(stmt)).scalars().all()
    for binding in bindings:
        duplicated = select(RolePermission).where(
            RolePermission.empresa_id == binding.empresa_id,
            RolePermission.role_id == binding.role_id,
            RolePermission.permission_id == target.id,
        )
        result = await session.execute(duplicated)
        if result.scalar_one_or_none() is None:
            session.add(
                RolePermission(
                    empresa_id=binding.empresa_id,
                    role_id=binding.role_id,
                    permission_id=target.id,
                )
            )
    await session.flush()


async def rename_legacy_permissions(session: AsyncSession) -> int:
    renamed = 0
    for legacy_name, current_name in LEGACY_RENAMES.items():
        stmt = select(Permission).where(Permission.name == legacy_name)
        legacy_permissions = (await session.execute(stmt)).scalars().all()
        for permission in legacy_permissions:
            target_stmt = select(Permission).where(
                Permission.empresa_id == permission.empresa_id,
                Permission.name == current_name,
            )
            target = (await session.execute(target_stmt)).scalar_one_or_none()
            if target is None:
                permission.name = current_name
                permission.deleted_at = None
                renamed += 1
                continue
            target.deleted_at = None
            await _move_bindings(session, permission, target)
            await session.execute(
                delete(RolePermission).where(
                    RolePermission.empresa_id == permission.empresa_id,
                    RolePermission.permission_id == permission.id,
                )
            )
            await session.execute(
                delete(Permission).where(Permission.id == permission.id)
            )
            renamed += 1
    return renamed


async def _get_or_create_empresa(
    session: AsyncSession,
    slug: str,
    name: str,
) -> Empresa:
    stmt = select(Empresa).where(Empresa.slug == slug)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        print(f"Empresa '{slug}' já existe (id={existing.id}).")
        return existing
    empresa = Empresa(name=name, slug=slug, is_active=True)
    session.add(empresa)
    await session.flush()
    print(f"Empresa '{slug}' criada (id={empresa.id}).")
    return empresa


async def _get_or_create_permission(
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
    if existing is not None:
        existing.deleted_at = None
        return existing
    permission = Permission(empresa_id=empresa_id, name=name)
    session.add(permission)
    await session.flush()
    print(f"  Permission '{name}' criada (id={permission.id}).")
    return permission


async def _get_or_create_role(
    session: AsyncSession,
    empresa_id: int,
    name: str,
    description: str,
) -> Role:
    stmt = select(Role).where(Role.empresa_id == empresa_id, Role.name == name)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        existing.deleted_at = None
        return existing
    role = Role(empresa_id=empresa_id, name=name, description=description)
    session.add(role)
    await session.flush()
    print(f"  Role '{name}' criada (id={role.id}).")
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
    session.add(
        RolePermission(
            empresa_id=empresa_id,
            role_id=role_id,
            permission_id=permission_id,
        )
    )


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
    session.add(
        UserRole(
            empresa_id=empresa_id,
            user_id=user_id,
            role_id=role_id,
        )
    )


async def _ensure_first_admin(
    session: AsyncSession,
    empresa_id: int,
    admin_role_id: int,
    email: str | None,
    password: str | None,
    full_name: str,
) -> None:
    stmt = select(func.count()).select_from(User)
    total_users = (await session.execute(stmt)).scalar_one()
    if total_users > 0:
        print(
            "Usuários já existem no banco: administrador não foi criado nem alterado."
        )
        return
    if not email or not password:
        raise BootstrapConfigError(
            "Não há usuários no banco e "
            f"{ENV_ADMIN_EMAIL} / {ENV_ADMIN_PASSWORD} não foram definidos."
        )
    user = User(
        empresa_id=empresa_id,
        email=email,
        password_hash=get_password_hash(password),
        full_name=full_name,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    await _assign_role_to_user(session, empresa_id, user.id, admin_role_id)
    print(f"Administrador '{email}' criado com o perfil 'admin'.")


async def bootstrap(
    session: AsyncSession,
    *,
    empresa_slug: str,
    empresa_name: str,
    admin_email: str | None,
    admin_password: str | None,
    admin_full_name: str,
) -> int:
    renamed = await rename_legacy_permissions(session)

    empresa = await _get_or_create_empresa(session, empresa_slug, empresa_name)

    print("\n--- Criando permissions ---")
    perm_map: dict[str, Permission] = {}
    for name in ALL_PERMISSIONS:
        perm_map[name] = await _get_or_create_permission(session, empresa.id, name)

    print("\n--- Criando roles ---")
    profiles: dict[str, Role] = {}
    for name, description in PROFILES:
        profiles[name] = await _get_or_create_role(
            session, empresa.id, name, description
        )

    print("\n--- Atribuindo permissions aos roles ---")
    for permission in perm_map.values():
        await _assign_permission(
            session, empresa.id, profiles["admin"].id, permission.id
        )

    for name in ALL_PERMISSIONS:
        if name in MANAGER_EXCLUDED:
            continue
        await _assign_permission(
            session, empresa.id, profiles["manager"].id, perm_map[name].id
        )

    for name in READ_PERMISSIONS:
        await _assign_permission(
            session, empresa.id, profiles["viewer"].id, perm_map[name].id
        )

    print("\n--- Garantindo primeiro administrador ---")
    await _ensure_first_admin(
        session,
        empresa.id,
        profiles["admin"].id,
        admin_email,
        admin_password,
        admin_full_name,
    )

    await session.commit()
    print(f"Bootstrap concluído ({renamed} permissões renomeadas).")
    return renamed


def _env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


def main() -> None:
    empresa_slug = _env(ENV_EMPRESA_SLUG)
    if empresa_slug is None:
        raise SystemExit(f"{ENV_EMPRESA_SLUG} não definida.")

    empresa_name = _env(ENV_EMPRESA_NAME) or empresa_slug
    admin_full_name = _env(ENV_ADMIN_NAME) or "Administrador"

    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def _run() -> None:
        async with session_factory() as session:
            await bootstrap(
                session,
                empresa_slug=empresa_slug,
                empresa_name=empresa_name,
                admin_email=_env(ENV_ADMIN_EMAIL),
                admin_password=_env(ENV_ADMIN_PASSWORD),
                admin_full_name=admin_full_name,
            )

    try:
        asyncio.run(_run())
    except BootstrapConfigError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
