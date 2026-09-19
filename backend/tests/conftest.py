from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from urllib.parse import urlparse, urlunparse

import asyncpg
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.database import get_db_session
from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.main import app


def _get_test_database_url() -> str:
    parsed = urlparse(settings.database_url)
    path = parsed.path
    if path.endswith("_test"):
        return settings.database_url
    test_path = path + "_test"
    return urlunparse(parsed._replace(path=test_path))


_test_database_url = _get_test_database_url()

_test_db_name = urlparse(_test_database_url).path.lstrip("/")


@pytest_asyncio.fixture(loop_scope="session")
async def client() -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(loop_scope="session")
async def _ensure_test_db():
    parsed = urlparse(settings.database_url)
    admin_url = urlunparse(parsed._replace(path="/postgres")).replace("+asyncpg", "")
    conn = await asyncpg.connect(admin_url)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            _test_db_name,
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{_test_db_name}"')
    finally:
        await conn.close()


@pytest_asyncio.fixture
async def db_session(_ensure_test_db) -> AsyncGenerator[AsyncSession]:
    engine: AsyncEngine = create_async_engine(
        _test_database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        await session.execute(text(f"SET timezone TO '{settings.app_timezone}'"))
        app.dependency_overrides[get_db_session] = lambda: session
        yield session
        app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_tenant(db_session: AsyncSession) -> Tenant:
    tenant = Tenant(
        name="Test Tenant",
        slug="test-tenant",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def test_user(
    db_session: AsyncSession,
    test_tenant: Tenant,
) -> User:
    user = User(
        tenant_id=test_tenant.id,
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def authenticated_headers(
    test_user: User,
    test_tenant: Tenant,
) -> dict[str, str]:
    token = create_access_token(
        data={
            "sub": str(test_user.id),
            "tenant_id": str(test_tenant.id),
        }
    )
    return {"Authorization": f"Bearer {token}"}
