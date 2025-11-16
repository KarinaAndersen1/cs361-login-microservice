from fastapi import APIRouter

from ..config import settings
from ..models import DiscoveryDocument
from ..security import build_symmetric_jwk

router = APIRouter(tags=["oidc"])


@router.get("/.well-known/openid-configuration", response_model=DiscoveryDocument)
def openid_configuration() -> DiscoveryDocument:
    base = settings.issuer_url.rstrip("/")
    return DiscoveryDocument(
        issuer=base,
        authorization_endpoint=f"{base}/oauth2/authorize",  # not fully implemented
        token_endpoint=f"{base}/oauth2/token",
        jwks_uri=f"{base}/oidc/jwks",
        userinfo_endpoint=f"{base}/oauth2/userinfo",
        response_types_supported=["token", "id_token", "none"],
        subject_types_supported=["public"],
        id_token_signing_alg_values_supported=[settings.jwt_algorithm],
        scopes_supported=["openid", "profile"],
        token_endpoint_auth_methods_supported=["none"],
        grant_types_supported=["password", "refresh_token"],
    )


@router.get("/oidc/jwks")
def jwks() -> dict:
    """
    JWKS endpoint. For demo purposes we expose the symmetric key as an 'oct' JWK.
    """
    return {"keys": [build_symmetric_jwk()]}
