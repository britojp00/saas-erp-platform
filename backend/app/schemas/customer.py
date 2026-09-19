from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from app.core.config import settings


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    document: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    notes: str | None = Field(default=None, max_length=5000)


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    document: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    notes: str | None = Field(default=None, max_length=5000)


class CustomerResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    document: str | None
    email: str | None
    phone: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()

    @field_serializer("updated_at")
    def _serialize_updated_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()


class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    page: int
    page_size: int
    total: int
