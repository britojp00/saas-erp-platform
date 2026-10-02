from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer, field_validator

from app.core.config import settings


class MovimentacaoCriarPayload(BaseModel):
    produto_id: int
    tipo_movimentacao: str = Field(pattern=r"^(ENTRADA|SAIDA|AJUSTE)$")
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


class MovimentacaoResposta(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int
    produto_id: int
    tipo_movimentacao: str
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


class ListaMovimentacoesResposta(BaseModel):
    items: list[MovimentacaoResposta]
    page: int
    page_size: int
    total: int


class ReservaCriarPayload(BaseModel):
    produto_id: int
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


class ReservaResposta(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int
    produto_id: int
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


class ListaReservasResposta(BaseModel):
    items: list[ReservaResposta]
    page: int
    page_size: int
    total: int


class EstoqueResposta(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int
    produto_id: int
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


class ListaEstoquesResposta(BaseModel):
    items: list[EstoqueResposta]
    page: int
    page_size: int
    total: int


class ConfirmarReservaResposta(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int
    produto_id: int
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
