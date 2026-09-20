from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_permissions
from app.db.database import get_db_session
from app.schemas.audit_log import AuditLogListResponse, AuditLogResponse
from app.services.audit_log import AuditLogService

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

SORT_FIELDS = {"action", "entity_type", "entity_id", "user_id", "created_at"}
ORDER_VALUES = {"asc", "desc"}


async def get_audit_log_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuditLogService:
    return AuditLogService(db)


@router.get(
    "",
    response_model=AuditLogListResponse,
    dependencies=[
        Depends(require_permissions("role.read")),
    ],
)
async def list_audit_logs(
    current_user: CurrentUser,
    service: Annotated[AuditLogService, Depends(get_audit_log_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    action: str | None = Query(default=None, max_length=50),
    entity_type: str | None = Query(default=None, max_length=100),
    entity_id: int | None = Query(default=None),
    user_id: int | None = Query(default=None),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
) -> AuditLogListResponse:
    if sort not in SORT_FIELDS:
        sort = "created_at"
    if order not in ORDER_VALUES:
        order = "desc"

    items, total = await service.list(
        current_user.tenant_id,
        page=page,
        page_size=page_size,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        sort=sort,
        order=order,
    )
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )
