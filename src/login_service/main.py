from fastapi import FastAPI

from .config import settings
from .logging_config import configure_logging, get_logger
from .routes import auth_router, health_router, oidc_router

configure_logging()
logger = get_logger("login_service.main")

app = FastAPI(title=settings.service_name)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Starting %s (issuer=%s)", settings.service_name, settings.issuer_url)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("Shutting down %s", settings.service_name)


app.include_router(health_router)
app.include_router(oidc_router)
app.include_router(auth_router)
