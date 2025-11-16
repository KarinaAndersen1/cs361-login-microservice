def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "service" in data


def test_discovery_document(client):
    resp = client.get("/.well-known/openid-configuration")
    assert resp.status_code == 200
    data = resp.json()
    assert data["issuer"].startswith("http://")
    assert "token_endpoint" in data
    assert "jwks_uri" in data
    assert "userinfo_endpoint" in data
    assert "password" in data["grant_types_supported"]


def test_jwks(client):
    resp = client.get("/oidc/jwks")
    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    assert len(data["keys"]) >= 1
    key = data["keys"][0]
    assert key["kty"] == "oct"
    assert key["use"] == "sig"
    assert "k" in key


def test_password_grant_and_userinfo_flow(client):
    # Login with demo user
    body = {
        "grant_type": "password",
        "username": "alice",
        "password": "password123",
        "client_id": "demo-client",
        "scope": "openid profile",
    }
    token_resp = client.post("/oauth2/token", json=body)
    assert token_resp.status_code == 200
    tokens = token_resp.json()
    assert "access_token" in tokens
    assert "id_token" in tokens
    assert "refresh_token" in tokens

    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # Call userinfo
    userinfo_resp = client.get(
        "/oauth2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert userinfo_resp.status_code == 200
    info = userinfo_resp.json()
    assert info["sub"] == "alice"
    assert info["preferred_username"] == "alice"

    # Refresh
    refresh_body = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": "demo-client",
    }
    refresh_resp = client.post("/oauth2/token", json=refresh_body)
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert "access_token" in new_tokens
    assert "id_token" in new_tokens
    assert "refresh_token" in new_tokens
