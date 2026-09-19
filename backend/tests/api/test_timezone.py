from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.tenant import Tenant
from app.db.models.user import User


@pytest.mark.asyncio
async def test_api_returns_timezone_aware_timestamps(
    client: AsyncClient,
    test_user: User,
    authenticated_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/auth/me",
        headers=authenticated_headers,
    )
    assert response.status_code == 200
    data = response.json()
    created_at = data["created_at"]
    assert created_at.endswith("-03:00"), (
        f"Expected Sao Paulo offset (-03:00), got: {created_at}"
    )


@pytest.mark.asyncio
async def test_postgres_uses_configured_timezone(
    db_session: AsyncSession,
):
    result = await db_session.execute(text("SHOW timezone"))
    db_tz = result.scalar()
    assert db_tz == settings.app_timezone, (
        f"Expected {settings.app_timezone}, got {db_tz}"
    )


@pytest.mark.asyncio
async def test_inserted_timestamp_preserves_instant(
    db_session: AsyncSession,
    test_tenant: Tenant,
):
    utc_now = datetime.now(UTC)
    user = User(
        tenant_id=test_tenant.id,
        email="tz-test@example.com",
        password_hash="fakehash",
        full_name="TZ Test User",
        is_active=True,
        created_at=utc_now,
        updated_at=utc_now,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.created_at is not None
    assert user.created_at.tzinfo is not None
    original_utc = utc_now.replace(tzinfo=UTC)
    assert user.created_at == original_utc, (
        "Temporal instant must be preserved after round-trip"
    )


@pytest.mark.asyncio
async def test_no_naive_datetimes_in_response(
    client: AsyncClient,
    test_user: User,
    authenticated_headers: dict[str, str],
):
    response = await client.get(
        "/api/v1/auth/me",
        headers=authenticated_headers,
    )
    assert response.status_code == 200
    data = response.json()
    created_at = data["created_at"]
    assert "+" in created_at or "-" in created_at, (
        f"Timestamp must include timezone offset, got: {created_at}"
    )
    assert not created_at.endswith("Z"), (
        f"Timestamp should use offset format, not Zulu: {created_at}"
    )
