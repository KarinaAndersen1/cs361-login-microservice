# Login Microservice

This microservice implements a simplified authentication and token
service similar to a lightweight OpenID Connect provider. It supports:

-   Password login\
-   Access token + refresh token issuance\
-   Userinfo retrieval\
-   Token refresh flow\
-   Standard JSON API endpoints\
-   Full automated test suite

This service is designed to be called by other microservices or
frontends in the CS361 ecosystem.

# Running the Microservice

Install dependencies:

``` bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Start the service:

``` bash
uvicorn login_service.main:app --host 0.0.0.0 --port 8000 --app-dir src
```

Open the interactive API documentation:

    http://localhost:8000/docs

------------------------------------------------------------------------

# Running Tests

A full integration test suite is included:

``` bash
pytest -q
```

------------------------------------------------------------------------

# API Endpoints & How to Use Them

This section explains **exactly how to request and receive data**, with
example calls.

------------------------------------------------------------------------

## 1. Health Check

**Endpoint**

``` http
GET /health
```

**Response**

``` json
{
  "status": "ok",
  "service": "login-service"
}
```

------------------------------------------------------------------------

## 2. OIDC Discovery Document

**Endpoint**

``` http
GET /.well-known/openid-configuration
```

**Example Response (truncated)**

``` json
{
  "issuer": "http://localhost:8000",
  "token_endpoint": "http://localhost:8000/oauth2/token",
  "userinfo_endpoint": "http://localhost:8000/oauth2/userinfo",
  "jwks_uri": "http://localhost:8000/oidc/jwks"
}
```

------------------------------------------------------------------------

## 3. Request Access + Refresh Tokens (Password Login)

**Endpoint**

``` http
POST /oauth2/token
```

**Request Body**

``` json
{
  "grant_type": "password",
  "username": "alice",
  "password": "password123",
  "client_id": "demo-client",
  "scope": "openid profile"
}
```

**Example `curl`**

``` bash
curl -X POST "http://localhost:8000/oauth2/token" \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "password",
    "username": "alice",
    "password": "password123",
    "client_id": "demo-client",
    "scope": "openid profile"
  }'
```

**Example Response**

``` json
{
  "access_token": "ACCESS_TOKEN_VALUE",
  "refresh_token": "REFRESH_TOKEN_VALUE",
  "token_type": "Bearer",
  "expires_in": 1800,
  "scope": "openid profile"
}
```

------------------------------------------------------------------------

## 4. Retrieve User Info With an Access Token

You can authenticate using:

### Option A --- Authorization header

    Authorization: Bearer ACCESS_TOKEN_VALUE

### Option B --- Query parameter (helpful in Swagger)

    /oauth2/userinfo?access_token=ACCESS_TOKEN_VALUE

**Example `curl` with header**

``` bash
curl "http://localhost:8000/oauth2/userinfo" \
  -H "Authorization: Bearer ACCESS_TOKEN_VALUE"
```

**Example `curl` with query param**

``` bash
curl "http://localhost:8000/oauth2/userinfo?access_token=ACCESS_TOKEN_VALUE"
```

**Example Response**

``` json
{
  "sub": "alice",
  "preferred_username": "alice",
  "name": "Alice"
}
```

------------------------------------------------------------------------

## 5. Refresh Token Flow

**Endpoint**

``` http
POST /oauth2/token
```

**Request Body**

``` json
{
  "grant_type": "refresh_token",
  "refresh_token": "REFRESH_TOKEN_VALUE",
  "client_id": "demo-client"
}
```

**Example `curl`**

``` bash
curl -X POST "http://localhost:8000/oauth2/token" \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "refresh_token",
    "refresh_token": "REFRESH_TOKEN_VALUE",
    "client_id": "demo-client"
  }'
```

**Response**

``` json
{
  "access_token": "NEW_ACCESS_TOKEN",
  "refresh_token": "NEW_REFRESH_TOKEN",
  "token_type": "Bearer"
}
```

------------------------------------------------------------------------

# How Another Microservice Would Use This

1.  Send username/password to:

        POST /oauth2/token

2.  Store the returned `access_token` and `refresh_token`.

3.  To authenticate requests, include:

        Authorization: Bearer ACCESS_TOKEN

4.  To get user info:

        GET /oauth2/userinfo

5.  To refresh tokens:

        POST /oauth2/token  (grant_type=refresh_token)

This microservice acts as the **authentication broker** for your system.

-----------------------------------------------------------------------

# Test Program (Example of How to Call This Microservice)

The following Python program demonstrates how another microservice or main program can send requests to this Login Microservice and receive the returned data.
This fulfills the requirement for a test program written in a programming language (not curl, not Postman).

Save this as test_program.py and run it with:

python test_program.py

**Test Program Code (Python)**
``` python
import requests

BASE_URL = "http://localhost:8000"

def main():
    # ---- 1. Request access + refresh tokens ----
    print("Requesting tokens...")

    token_response = requests.post(
        f"{BASE_URL}/oauth2/token",
        json={
            "grant_type": "password",
            "username": "alice",
            "password": "password123",
            "client_id": "demo-client",
            "scope": "openid profile"
        }
    )

    if token_response.status_code != 200:
        print("Error getting tokens:", token_response.text)
        return

    tokens = token_response.json()
    print("Token Response:", tokens)

    access_token = tokens["access_token"]

    # ---- 2. Use access token to call /userinfo ----
    print("\nCalling userinfo...")

    userinfo_response = requests.get(
        f"{BASE_URL}/oauth2/userinfo",
        params={"access_token": access_token}
    )

    if userinfo_response.status_code != 200:
        print("Error calling userinfo:", userinfo_response.text)
        return

    print("Userinfo Response:", userinfo_response.json())


if __name__ == "__main__":
    main()
```

------------------------------------------------------------------------

## Authentication Sequence Diagram

```mermaid
sequenceDiagram
    participant Client as Program making a request
    participant Service as Login microservice
    participant Store as Token store<br/>(ACCESS_TOKENS / REFRESH_TOKENS)

    Note left of Client: User enters\nusername & password
    loop login attempts
        Client->>Service: POST /oauth2/token\n(grant_type=password,\nusername, password,\nclient_id, scope)
        Service->>Service: validate client_id\nand request fields
        Service->>Service: check credentials\n(e.g., alice / password123)
        alt credentials valid
            Service->>Store: save access_token\nand refresh_token for user
            Service-->>Client: 200 OK\n{access_token, refresh_token,\nexpires_in, scope}
        else credentials invalid
            Service-->>Client: 401 Unauthorized\n{"detail": "Invalid username or password"}
        end
    end

    loop use access token
        Client->>Service: GET /oauth2/userinfo\n(access_token in query\nor Authorization header)
        Service->>Store: look up access_token
        alt token found
            Service-->>Client: 200 OK\n{sub, preferred_username, name}
        else token not found
            Service-->>Client: 401 Unauthorized\n{"detail": "Invalid or expired access token"}
        end
    end

    opt refresh token flow
        Client->>Service: POST /oauth2/token\n(grant_type=refresh_token,\nrefresh_token, client_id)
        Service->>Store: look up refresh_token
        alt refresh token valid
            Service->>Store: generate & store\nnew access_token and refresh_token
            Service-->>Client: 200 OK\n{new access_token,\nnew refresh_token}
        else refresh token invalid
            Service-->>Client: 401 Unauthorized\n{"detail": "Invalid refresh token"}
        end
    end
