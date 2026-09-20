import logging

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.db.models.tenant import Tenant
from app.db.models.user import User


def _find_record(caplog, event_name: str):
    for record in caplog.records:
        if getattr(record, "event", None) == event_name:
            return record
    return None


def _find_records(caplog, event_name: str):
    return [r for r in caplog.records if getattr(r, "event", None) == event_name]


# --- REQUEST ID ---


@pytest.mark.asyncio
async def test_request_without_id_generates_uuid(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    request_id = response.headers.get("x-request-id")
    assert request_id is not None
    assert len(request_id) == 36
    assert request_id.count("-") == 4


@pytest.mark.asyncio
async def test_response_contains_x_request_id(client: AsyncClient):
    response = await client.get("/health")
    assert "x-request-id" in response.headers


@pytest.mark.asyncio
async def test_request_with_valid_id_preserves_it(client: AsyncClient):
    custom_id = "550e8400-e29b-41d4-a716-446655440000"
    response = await client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.headers.get("x-request-id") == custom_id


@pytest.mark.asyncio
async def test_different_requests_get_different_ids(client: AsyncClient):
    r1 = await client.get("/health")
    r2 = await client.get("/health")
    id1 = r1.headers.get("x-request-id")
    id2 = r2.headers.get("x-request-id")
    assert id1 != id2


@pytest.mark.asyncio
async def test_oversized_request_id_generates_new_uuid(client: AsyncClient):
    huge_id = "a" * 200
    response = await client.get("/health", headers={"X-Request-ID": huge_id})
    generated_id = response.headers.get("x-request-id")
    assert generated_id is not None
    assert generated_id != huge_id
    assert len(generated_id) == 36


# --- HTTP LOGGING ---


@pytest.mark.asyncio
async def test_request_generates_log(
    client: AsyncClient,
    caplog: pytest.LogCaptureFixture,
):
    with caplog.at_level(logging.INFO, logger="app.http"):
        await client.get("/health")
    record = _find_record(caplog, "request_completed")
    assert record is not None


@pytest.mark.asyncio
async def test_log_contains_method(
    client: AsyncClient,
    caplog: pytest.LogCaptureFixture,
):
    with caplog.at_level(logging.INFO, logger="app.http"):
        await client.get("/health")
    record = _find_record(caplog, "request_completed")
    assert record is not None
    assert record.method == "GET"


@pytest.mark.asyncio
async def test_log_contains_path(
    client: AsyncClient,
    caplog: pytest.LogCaptureFixture,
):
    with caplog.at_level(logging.INFO, logger="app.http"):
        await client.get("/health")
    record = _find_record(caplog, "request_completed")
    assert record is not None
    assert record.path == "/health"


@pytest.mark.asyncio
async def test_log_contains_status_code(
    client: AsyncClient,
    caplog: pytest.LogCaptureFixture,
):
    with caplog.at_level(logging.INFO, logger="app.http"):
        await client.get("/health")
    record = _find_record(caplog, "request_completed")
    assert record is not None
    assert record.status_code == 200


@pytest.mark.asyncio
async def test_log_contains_duration_ms(
    client: AsyncClient,
    caplog: pytest.LogCaptureFixture,
):
    with caplog.at_level(logging.INFO, logger="app.http"):
        await client.get("/health")
    record = _find_record(caplog, "request_completed")
    assert record is not None
    assert record.duration_ms is not None
    assert isinstance(record.duration_ms, (int, float))


@pytest.mark.asyncio
async def test_log_contains_request_id(
    client: AsyncClient,
    caplog: pytest.LogCaptureFixture,
):
    with caplog.at_level(logging.INFO, logger="app.http"):
        await client.get("/health")
    record = _find_record(caplog, "request_completed")
    assert record is not None
    assert record.request_id is not None


# --- ERRORS ---


@pytest.mark.asyncio
async def test_401_has_request_id(client: AsyncClient):
    response = await client.get("/api/v1/customers/999999")
    assert response.status_code == 401
    assert "x-request-id" in response.headers


@pytest.mark.asyncio
async def test_unexpected_error_does_not_expose_traceback(client: AsyncClient):
    response = await client.get("/api/v1/customers/999999")
    assert response.status_code == 401
    body = response.json()
    assert "traceback" not in str(body).lower()
    assert "exception" not in str(body).lower()


# --- SECURITY ---


@pytest.mark.asyncio
async def test_password_not_in_logs(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    caplog: pytest.LogCaptureFixture,
):
    with caplog.at_level(logging.INFO):
        await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
    for record in caplog.records:
        assert "testpassword123" not in record.getMessage()


@pytest.mark.asyncio
async def test_jwt_not_in_logs(
    client: AsyncClient,
    test_tenant: Tenant,
    test_user: User,
    caplog: pytest.LogCaptureFixture,
):
    token = create_access_token(
        data={"sub": str(test_user.id), "tenant_id": str(test_tenant.id)}
    )
    with caplog.at_level(logging.INFO):
        await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    for record in caplog.records:
        assert token not in record.getMessage()


@pytest.mark.asyncio
async def test_authorization_header_not_in_logs(
    client: AsyncClient,
    db_session: AsyncSession,
    caplog: pytest.LogCaptureFixture,
):
    with caplog.at_level(logging.INFO):
        await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer faketoken123"},
        )
    for record in caplog.records:
        assert "faketoken123" not in record.getMessage()


@pytest.mark.asyncio
async def test_secrets_not_in_logs(
    client: AsyncClient,
    caplog: pytest.LogCaptureFixture,
):
    with caplog.at_level(logging.INFO):
        await client.get("/health")
    for record in caplog.records:
        assert "jwt_secret_key" not in record.getMessage()
        assert "database_url" not in record.getMessage()


@pytest.mark.asyncio
async def test_request_body_not_logged(
    client: AsyncClient,
    authenticated_headers: dict,
    caplog: pytest.LogCaptureFixture,
):
    with caplog.at_level(logging.INFO):
        await client.post(
            "/api/v1/customers",
            headers=authenticated_headers,
            json={"name": "Body Test", "document": "12345678901"},
        )
    for record in caplog.records:
        assert "12345678901" not in record.getMessage()


# --- CONTEXT ---


@pytest.mark.asyncio
async def test_user_id_appears_when_authenticated(
    client: AsyncClient,
    authenticated_headers: dict,
    caplog: pytest.LogCaptureFixture,
):
    with caplog.at_level(logging.INFO, logger="app.http"):
        await client.get("/api/v1/auth/me", headers=authenticated_headers)
    record = _find_record(caplog, "request_completed")
    assert record is not None
    assert record.user_id is not None


@pytest.mark.asyncio
async def test_tenant_id_appears_when_authenticated(
    client: AsyncClient,
    authenticated_headers: dict,
    caplog: pytest.LogCaptureFixture,
):
    with caplog.at_level(logging.INFO, logger="app.http"):
        await client.get("/api/v1/auth/me", headers=authenticated_headers)
    record = _find_record(caplog, "request_completed")
    assert record is not None
    assert record.tenant_id is not None


@pytest.mark.asyncio
async def test_context_not_leaked_between_requests(
    client: AsyncClient,
    test_tenant: Tenant,
    test_user: User,
    caplog: pytest.LogCaptureFixture,
):
    token = create_access_token(
        data={"sub": str(test_user.id), "tenant_id": str(test_tenant.id)}
    )
    with caplog.at_level(logging.INFO, logger="app.http"):
        await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.get("/health")
    health_records = [
        r
        for r in caplog.records
        if getattr(r, "event", None) == "request_completed"
        and getattr(r, "path", None) == "/health"
    ]
    assert len(health_records) > 0
    last = health_records[-1]
    assert last.user_id is None
    assert last.tenant_id is None
