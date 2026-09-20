import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware import HTTPLoggingMiddleware
from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.customers import router as customers_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.orders import router as orders_router
from app.api.v1.products import router as products_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging

setup_logging(level=settings.log_level, json_format=settings.log_json)

logger = logging.getLogger("app")

app = FastAPI(
    title="SaaS ERP Platform",
    version="0.1.0",
    description="ERP SaaS multi-tenant desenvolvido com Python e FastAPI.",
)

app.add_middleware(HTTPLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(audit_logs_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(customers_router, prefix="/api/v1")
app.include_router(inventory_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event() -> None:
    logger.info(
        "application_started",
        extra={
            "event": "application_started",
            "environment": settings.app_env,
            "version": settings.app_version,
        },
    )


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info(
        "application_shutdown",
        extra={"event": "application_shutdown"},
    )


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "saas-erp-platform",
    }
