from datetime import datetime

from pydantic import BaseModel, field_serializer

from app.core.config import settings


class AuditLogResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    description: str | None
    old_values: dict | None
    new_values: dict | None
    created_at: datetime

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    page: int
    page_size: int
    total: int
