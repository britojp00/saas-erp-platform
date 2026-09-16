from fastapi import FastAPI

app = FastAPI(
    title="SaaS ERP Platform",
    version="0.1.0",
    description="ERP SaaS multi-tenant desenvolvido com Python e FastAPI.",
)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "saas-erp-platform",
    }
