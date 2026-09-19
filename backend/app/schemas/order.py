from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer, field_validator

from app.core.config import settings


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: Decimal = Field(max_digits=15, decimal_places=3)
    unit_price: Decimal | None = Field(default=None, max_digits=15, decimal_places=2)

    @field_validator("quantity")
    @classmethod
    def _validate_quantity(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("A quantidade deve ser maior que zero")
        return v

    @field_validator("unit_price")
    @classmethod
    def _validate_unit_price(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v < 0:
            raise ValueError("O preço unitário não pode ser negativo")
        return v


class OrderItemUpdate(BaseModel):
    quantity: Decimal | None = Field(default=None, max_digits=15, decimal_places=3)
    unit_price: Decimal | None = Field(default=None, max_digits=15, decimal_places=2)

    @field_validator("quantity")
    @classmethod
    def _validate_quantity(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("A quantidade deve ser maior que zero")
        return v

    @field_validator("unit_price")
    @classmethod
    def _validate_unit_price(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v < 0:
            raise ValueError("O preço unitário não pode ser negativo")
        return v


class OrderCreate(BaseModel):
    customer_id: int
    notes: str | None = Field(default=None, max_length=1000)
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderUpdate(BaseModel):
    customer_id: int | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=1000)


class OrderItemResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int
    order_id: int
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    created_at: datetime
    updated_at: datetime

    @field_serializer("quantity")
    def _serialize_quantity(self, value: Decimal, _info) -> float:
        return float(value)

    @field_serializer("unit_price")
    def _serialize_unit_price(self, value: Decimal, _info) -> float:
        return float(value)

    @field_serializer("total_price")
    def _serialize_total_price(self, value: Decimal, _info) -> float:
        return float(value)

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()

    @field_serializer("updated_at")
    def _serialize_updated_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()


class OrderResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int
    order_number: int
    customer_id: int
    status: str
    total_amount: Decimal
    notes: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    items: list[OrderItemResponse] = Field(default_factory=list)

    @field_serializer("total_amount")
    def _serialize_total_amount(self, value: Decimal, _info) -> float:
        return float(value)

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


class OrderListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int
    order_number: int
    customer_id: int
    status: str
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime

    @field_serializer("total_amount")
    def _serialize_total_amount(self, value: Decimal, _info) -> float:
        return float(value)

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()

    @field_serializer("updated_at")
    def _serialize_updated_at(self, value: datetime, _info) -> str:
        return value.astimezone(settings.tz).isoformat()


class OrderListResponse(BaseModel):
    items: list[OrderListItem]
    page: int
    page_size: int
    total: int
