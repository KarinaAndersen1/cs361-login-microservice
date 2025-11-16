from typing import List, Optional

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    scope: Optional[str] = None


class UserInfoResponse(BaseModel):
    sub: str
    preferred_username: str
    name: Optional[str] = None


class DiscoveryDocument(BaseModel):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    userinfo_endpoint: str
    response_types_supported: List[str]
    subject_types_supported: List[str]
    id_token_signing_alg_values_supported: List[str]
    scopes_supported: List[str]
    token_endpoint_auth_methods_supported: List[str]
    grant_types_supported: List[str]
