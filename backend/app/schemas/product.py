from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer, field_validator

from app.core.config import settings


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    category_id: int | None = Field(default=None)
    price: Decimal = Field(max_digits=15, decimal_places=2)
    cost_price: Decimal | None = Field(default=None, max_digits=15, decimal_places=2)
    is_active: bool = Field(default=True)

    @field_validator("price")
    @classmethod
    def _validate_price(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("O preço não pode ser negativo")
        return v

    @field_validator("cost_price")
    @classmethod
    def _validate_cost_price(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v < 0:
            raise ValueError("O preço de custo não pode ser negativo")
        return v


class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    category_id: int | None = Field(default=None)
    price: Decimal | None = Field(default=None, max_digits=15, decimal_places=2)
    cost_price: Decimal | None = Field(default=None, max_digits=15, decimal_places=2)
    is_active: bool | None = Field(default=None)

    @field_validator("price")
    @classmethod
    def _validate_price(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v < 0:
            raise ValueError("O preço não pode ser negativo")
        return v

    @field_validator("cost_price")
    @classmethod
    def _validate_cost_price(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v < 0:
            raise ValueError("O preço de custo não pode ser negativo")
        return v


class ProductResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int
    sku: str
    name: str
    description: str | None
    category_id: int | None
    price: Decimal
    cost_price: Decimal | None
    is_active: bool
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


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    page: int
    page_size: int
    total: int
