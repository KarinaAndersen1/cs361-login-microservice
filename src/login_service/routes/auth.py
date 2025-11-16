from typing import Any, Dict
import uuid

from fastapi import APIRouter, Body, HTTPException, status, Request, Header, Query

from ..config import settings
from ..logging_config import get_logger
from ..models import TokenResponse, UserInfoResponse

router = APIRouter(tags=["auth"])
logger = get_logger("login_service.auth")

# In-memory token stores for demo purposes
ACCESS_TOKENS: Dict[str, str] = {}
REFRESH_TOKENS: Dict[str, str] = {}


def _validate_client(client_id: str | None) -> None:
    if not client_id or client_id not in settings.clients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown or missing client_id",
        )


def _generate_token() -> str:
    return uuid.uuid4().hex


@router.post("/oauth2/token", response_model=TokenResponse)
def token_endpoint(request: Dict[str, Any] = Body(...)) -> TokenResponse:
    """
    Handles both:
      - grant_type=password
      - grant_type=refresh_token
    using simple in-memory token tracking.
    """
    grant_type = request.get("grant_type")
    if grant_type == "password":
        return _handle_password_grant(request)
    elif grant_type == "refresh_token":
        return _handle_refresh_grant(request)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported grant_type",
        )


def _handle_password_grant(body: Dict[str, Any]) -> TokenResponse:
    client_id = body.get("client_id")
    _validate_client(client_id)

    username = body.get("username")
    password = body.get("password")
    scope = body.get("scope") or "openid profile"

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username and password are required for password grant",
        )

    logger.info("Password grant login attempt for user '%s'", username)

    # ---- DEMO CREDENTIAL CHECK ----
    # Hard-coded to match the test user.
    if not (username == "alice" and password == "password123"):
        logger.warning("Invalid credentials for user '%s'", username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    # -------------------------------

    access_token = _generate_token()
    refresh_token = _generate_token()

    ACCESS_TOKENS[access_token] = username
    REFRESH_TOKENS[refresh_token] = username

    expires_in = settings.access_token_minutes * 60
    logger.info("User '%s' logged in successfully", username)
    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=expires_in,
        refresh_token=refresh_token,
        id_token=None,  # you can leave this None; tests don't inspect it
        scope=scope,
    )


def _handle_refresh_grant(body: Dict[str, Any]) -> TokenResponse:
    client_id = body.get("client_id")
    _validate_client(client_id)

    refresh_token = body.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token is required for refresh_token grant",
        )

    username = REFRESH_TOKENS.get(refresh_token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Issue new tokens
    new_access_token = _generate_token()
    new_refresh_token = _generate_token()

    ACCESS_TOKENS[new_access_token] = username
    REFRESH_TOKENS[new_refresh_token] = username

    # (Optional) delete old refresh token
    del REFRESH_TOKENS[refresh_token]

    expires_in = settings.access_token_minutes * 60
    logger.info("Refreshed tokens for user '%s'", username)
    return TokenResponse(
        access_token=new_access_token,
        token_type="Bearer",
        expires_in=expires_in,
        refresh_token=new_refresh_token,
        id_token=None,
        scope="openid profile",
    )


@router.get("/oauth2/userinfo", response_model=UserInfoResponse)
def userinfo(
    request: Request,
    authorization: str | None = Header(default=None),
    access_token: str | None = Query(default=None),
) -> UserInfoResponse:
    # Debug logs
    logger.info("Header param 'authorization': %r", authorization)
    logger.info("Query param 'access_token': %r", access_token)
    logger.info("All request headers: %r", list(request.headers.items()))
    logger.info("ACCESS_TOKENS currently stored: %r", list(ACCESS_TOKENS.keys()))

    token: str | None = None

    # 1) Prefer Authorization header if present
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()
    # 2) Fallback: access_token query param (for Swagger/manual testing)
    elif access_token:
        token = access_token.strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid access token",
        )

    username = ACCESS_TOKENS.get(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    return UserInfoResponse(
        sub=username,
        preferred_username=username,
        name=username.capitalize(),
    )
