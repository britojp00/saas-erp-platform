from contextvars import ContextVar
from dataclasses import dataclass

_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
_empresa_id_var: ContextVar[int | None] = ContextVar("empresa_id", default=None)
_user_id_var: ContextVar[int | None] = ContextVar("user_id", default=None)


@dataclass(frozen=True, slots=True)
class RequestContext:
    request_id: str | None
    empresa_id: int | None
    user_id: int | None


def get_request_context() -> RequestContext:
    return RequestContext(
        request_id=_request_id_var.get(),
        empresa_id=_empresa_id_var.get(),
        user_id=_user_id_var.get(),
    )


def set_request_id(request_id: str | None) -> None:
    _request_id_var.set(request_id)


def set_empresa_id(empresa_id: int | None) -> None:
    _empresa_id_var.set(empresa_id)


def set_user_id(user_id: int | None) -> None:
    _user_id_var.set(user_id)


def clear_request_context() -> None:
    _request_id_var.set(None)
    _empresa_id_var.set(None)
    _user_id_var.set(None)
