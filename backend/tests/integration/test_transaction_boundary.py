from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import NamedTuple
from urllib.parse import urlparse, urlunparse

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.db.base import Base
from app.db.database import get_db_session
from app.db.models.customer import Customer
from app.db.models.tenant import Tenant


def _test_database_url() -> str:
    parsed = urlparse(settings.database_url)
    path = parsed.path
    if path.endswith("_test"):
        return settings.database_url
    return urlunparse(parsed._replace(path=path + "_test"))


class BoundaryFactories(NamedTuple):
    application: async_sessionmaker[AsyncSession]
    independent: async_sessionmaker[AsyncSession]


@pytest_asyncio.fixture
async def transaction_boundary(
    monkeypatch,
    _ensure_test_db,
) -> AsyncGenerator[BoundaryFactories]:
    app_engine = create_async_engine(
        _test_database_url(),
        echo=False,
        pool_pre_ping=True,
    )
    independent_engine = create_async_engine(
        _test_database_url(),
        echo=False,
        pool_pre_ping=True,
    )

    async with app_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    app_factory = async_sessionmaker(
        bind=app_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    independent_factory = async_sessionmaker(
        bind=independent_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    monkeypatch.setattr("app.db.database.async_session_factory", app_factory)

    yield BoundaryFactories(
        application=app_factory,
        independent=independent_factory,
    )

    async with app_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await app_engine.dispose()
    await independent_engine.dispose()


@pytest_asyncio.fixture
async def tenant_id(transaction_boundary: BoundaryFactories) -> int:
    async with transaction_boundary.application() as session:
        tenant = Tenant(
            name="Boundary Tenant",
            slug="boundary-tenant",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(tenant)
        await session.commit()
        return tenant.id


@asynccontextmanager
async def _boundary_session() -> AsyncGenerator[AsyncSession]:
    """Consome a fronteira transacional real (get_db_session)."""
    session_generator = get_db_session()
    session = await session_generator.asend(None)
    try:
        yield session
    except BaseException as error:
        await session_generator.athrow(error)
        raise
    else:
        try:
            await session_generator.asend(None)
        except StopAsyncIteration:
            pass


@pytest.mark.asyncio
async def test_commit_persists_record_on_normal_exit(
    transaction_boundary: BoundaryFactories,
    tenant_id: int,
) -> None:
    async with _boundary_session() as session:
        customer = Customer(
            tenant_id=tenant_id,
            name="Cliente Commit Boundary",
            document="BOUNDARY-COMMIT-001",
        )
        session.add(customer)
        await session.flush()
        assert customer.id is not None

    async with transaction_boundary.independent() as check_session:
        result = await check_session.execute(
            select(Customer).where(Customer.document == "BOUNDARY-COMMIT-001"),
        )
        persisted = result.scalar_one_or_none()

    assert persisted is not None
    assert persisted.name == "Cliente Commit Boundary"
    assert persisted.tenant_id == tenant_id


@pytest.mark.asyncio
async def test_rollback_discards_record_after_exception(
    transaction_boundary: BoundaryFactories,
    tenant_id: int,
) -> None:
    with pytest.raises(RuntimeError, match="falha após o flush"):
        async with _boundary_session() as session:
            customer = Customer(
                tenant_id=tenant_id,
                name="Cliente Rollback Boundary",
                document="BOUNDARY-ROLLBACK-001",
            )
            session.add(customer)
            await session.flush()
            assert customer.id is not None
            raise RuntimeError("falha após o flush")

    async with transaction_boundary.independent() as check_session:
        persisted = (
            await check_session.execute(
                select(Customer).where(
                    Customer.document == "BOUNDARY-ROLLBACK-001",
                ),
            )
        ).scalar_one_or_none()

    assert persisted is None

    async with transaction_boundary.independent() as check_session:
        tenant = await check_session.get(Tenant, tenant_id)

    assert tenant is not None
