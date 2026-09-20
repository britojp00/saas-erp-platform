import logging
import time
import uuid

import jwt
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings
from app.core.request_context import (
    clear_request_context,
    set_request_id,
    set_tenant_id,
    set_user_id,
)

logger = logging.getLogger("app.http")

MAX_REQUEST_ID_LENGTH = 128


def _extract_user_context(request: Request) -> tuple[int | None, int | None]:
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, None

    token = auth_header[7:]
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id_str = payload.get("sub")
        tenant_id_str = payload.get("tenant_id")
        user_id = int(user_id_str) if user_id_str else None
        tenant_id = int(tenant_id_str) if tenant_id_str else None
        return user_id, tenant_id
    except jwt.ExpiredSignatureError:
        return None, None
    except jwt.InvalidTokenError:
        return None, None


class HTTPLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("x-request-id", "").strip()
        if not request_id or len(request_id) > MAX_REQUEST_ID_LENGTH:
            request_id = str(uuid.uuid4())

        set_request_id(request_id)

        user_id, tenant_id = _extract_user_context(request)
        set_tenant_id(tenant_id)
        set_user_id(user_id)

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "request_failed",
                extra={
                    "event": "request_failed",
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            clear_request_context()
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        status_code = response.status_code
        if status_code >= 500:
            log_level = logging.ERROR
        elif status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO

        from app.core.request_context import get_request_context

        ctx = get_request_context()
        logger.log(
            log_level,
            "request_completed",
            extra={
                "event": "request_completed",
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "request_id": ctx.request_id,
                "user_id": ctx.user_id,
                "tenant_id": ctx.tenant_id,
            },
        )

        clear_request_context()

        return response
