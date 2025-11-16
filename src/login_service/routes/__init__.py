from .auth import router as auth_router
from .health import router as health_router
from .oidc import router as oidc_router

__all__ = ["auth_router", "health_router", "oidc_router"]
