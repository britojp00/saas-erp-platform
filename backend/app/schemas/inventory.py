from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer, field_validator

from app.core.config import settings


class MovementCreate(BaseModel):
    product_id: int
    movement_type: str = Field(pattern=r"^(IN|OUT|ADJUSTMENT)$")
    quantity: Decimal = Field(max_digits=15, decimal_places=3)
    reference: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=500)
    idempotency_key: str = Field(min_length=1, max_length=255)

    @field_validator("quantity")
    @classmethod
    def _validate_quantity(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("A quantidade deve ser maior que zero")
        return v


class MovementResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int
    product_id: int
    movement_type: str
    quantity: Decimal
    reference: str | None
    notes: str | None
    idempotency_key: str
    performed_at: datetime
    created_at: datetime
    updated_at: datetime

    @field_serializer("performed_at")
    def _serialize_performed_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()

    @field_serializer("updated_at")
    def _serialize_updated_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()


class MovementListResponse(BaseModel):
    items: list[MovementResponse]
    page: int
    page_size: int
    total: int


class ReservationCreate(BaseModel):
    product_id: int
    quantity: Decimal = Field(max_digits=15, decimal_places=3)
    reference: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=500)
    idempotency_key: str = Field(min_length=1, max_length=255)
    order_item_id: int | None = Field(default=None)

    @field_validator("quantity")
    @classmethod
    def _validate_quantity(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("A quantidade deve ser maior que zero")
        return v


class ReservationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int
    product_id: int
    quantity: Decimal
    status: str
    reference: str | None
    notes: str | None
    idempotency_key: str
    order_item_id: int | None
    reserved_at: datetime
    confirmed_at: datetime | None
    released_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_serializer("reserved_at")
    def _serialize_reserved_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()

    @field_serializer("confirmed_at")
    def _serialize_confirmed_at(self, value: datetime | None, _info) -> str | None:
        if value is None:
            return None
        return value.astimezone(settings.tz).isoformat()

    @field_serializer("released_at")
    def _serialize_released_at(self, value: datetime | None, _info) -> str | None:
        if value is None:
            return None
        return value.astimezone(settings.tz).isoformat()

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()

    @field_serializer("updated_at")
    def _serialize_updated_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()


class ReservationListResponse(BaseModel):
    items: list[ReservationResponse]
    page: int
    page_size: int
    total: int


class InventoryResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int
    product_id: int
    quantity: Decimal
    reserved_quantity: Decimal
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()

    @field_serializer("updated_at")
    def _serialize_updated_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()


class InventoryListResponse(BaseModel):
    items: list[InventoryResponse]
    page: int
    page_size: int
    total: int


class ConfirmReservationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int
    product_id: int
    quantity: Decimal
    status: str
    reference: str | None
    notes: str | None
    idempotency_key: str
    order_item_id: int | None
    reserved_at: datetime
    confirmed_at: datetime | None
    released_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_serializer("reserved_at")
    def _serialize_reserved_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()

    @field_serializer("confirmed_at")
    def _serialize_confirmed_at(self, value: datetime | None, _info) -> str | None:
        if value is None:
            return None
        return value.astimezone(settings.tz).isoformat()

    @field_serializer("released_at")
    def _serialize_released_at(self, value: datetime | None, _info) -> str | None:
        if value is None:
            return None
        return value.astimezone(settings.tz).isoformat()

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()

    @field_serializer("updated_at")
    def _serialize_updated_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()
