from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base exception for all application errors."""


class AuthenticationError(AppError):
    """Raised when authentication fails."""


class AuthorizationError(AppError):
    """Raised when the user lacks permission."""


class DomainError(AppError):
    """Base exception for business rule violations."""


class UserNotFoundError(DomainError):
    """Raised when a user is not found."""


class InactiveUserError(DomainError):
    """Raised when a user account is inactive."""


class DeletedUserError(DomainError):
    """Raised when a soft-deleted user attempts to authenticate."""


class TenantNotFoundError(DomainError):
    """Raised when a tenant is not found."""


class InactiveTenantError(DomainError):
    """Raised when a tenant is inactive."""


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"detail": "Credenciais inválidas"},
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"detail": "Acesso negado"},
        )

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_error_handler(
        request: Request, exc: UserNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": "Usuário não encontrado"},
        )

    @app.exception_handler(TenantNotFoundError)
    async def tenant_not_found_error_handler(
        request: Request, exc: TenantNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": "Tenant não encontrado"},
        )
