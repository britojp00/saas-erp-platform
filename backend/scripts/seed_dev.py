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
from app.db.models.tenant import Tenant
from app.db.models.user import User

engine = create_async_engine(settings.database_url, echo=False)
session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

SEED_TENANT_SLUG = "demo"
SEED_USER_EMAIL = "admin@demo.com"
DEFAULT_DEV_PASSWORD = "admin123"


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
            print(f"Usuário '{SEED_USER_EMAIL}' já existe (id={existing_user.id}).")
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

        await session.commit()
        print("Seed concluído com sucesso.")


if __name__ == "__main__":
    asyncio.run(seed())
