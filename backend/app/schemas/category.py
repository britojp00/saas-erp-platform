from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from app.core.config import settings


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=5000)
    parent_id: int | None = Field(default=None)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=5000)
    parent_id: int | None = Field(default=None)


class CategoryResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int
    name: str
    description: str | None
    parent_id: int | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()

    @field_serializer("updated_at")
    def _serialize_updated_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()

    @field_serializer("deleted_at")
    def _serialize_deleted_at(self, value: datetime | None, _info) -> str | None:
        if value is None:
            return None
        return value.astimezone(settings.tz).isoformat()


class CategoryListResponse(BaseModel):
    items: list[CategoryResponse]
    page: int
    page_size: int
    total: int
