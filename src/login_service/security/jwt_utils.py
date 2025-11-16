import base64
import datetime
from typing import Any, Dict, Optional

import jwt
from fastapi import Header, HTTPException, status

from ..config import settings


def _now_utc() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _encode(payload: Dict[str, Any], token_type: str) -> str:
    headers = {"kid": settings.jwt_key_id, "typ": "JWT"}
    payload = payload.copy()
    payload["typ"] = token_type
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        headers=headers,
    )


def create_id_token(
    subject: str,
    client_id: str,
    nonce: Optional[str] = None,
) -> str:
    now = _now_utc()
    exp = now + datetime.timedelta(minutes=settings.access_token_minutes)

    payload: Dict[str, Any] = {
        "iss": settings.issuer_url,
        "sub": subject,
        "aud": client_id,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if nonce:
        payload["nonce"] = nonce
    return _encode(payload, token_type="id")


def create_access_token(subject: str, scope: str = "openid profile") -> str:
    now = _now_utc()
    exp = now + datetime.timedelta(minutes=settings.access_token_minutes)
    payload = {
        "iss": settings.issuer_url,
        "sub": subject,
        "scope": scope,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return _encode(payload, token_type="access")


def create_refresh_token(subject: str) -> str:
    now = _now_utc()
    exp = now + datetime.timedelta(days=settings.refresh_token_days)
    payload = {
        "iss": settings.issuer_url,
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return _encode(payload, token_type="refresh")


def decode_token(token: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=None,
            options={"verify_aud": False},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    if expected_type and payload.get("typ") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    return payload


def get_current_username(
    authorization: str = Header(default="", alias="Authorization"),
) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_token(token, expected_type="access")
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    return username


def build_symmetric_jwk() -> Dict[str, Any]:
    """
    Expose the symmetric key as an octet sequence JWK (for demo purposes).
    """
    key_bytes = settings.jwt_secret.encode("utf-8")
    k = base64.urlsafe_b64encode(key_bytes).rstrip(b"=").decode("ascii")
    return {
        "kty": "oct",
        "kid": settings.jwt_key_id,
        "alg": settings.jwt_algorithm,
        "use": "sig",
        "k": k,
    }
