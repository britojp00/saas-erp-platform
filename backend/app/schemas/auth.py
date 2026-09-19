from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from app.core.config import settings


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str
    full_name: str
    is_active: bool
    tenant_id: int
    created_at: datetime
    roles: list[str]
    permissions: list[str]

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()
