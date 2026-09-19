from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.customers import router as customers_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers

app = FastAPI(
    title="SaaS ERP Platform",
    version="0.1.0",
    description="ERP SaaS multi-tenant desenvolvido com Python e FastAPI.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(customers_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "saas-erp-platform",
    }
