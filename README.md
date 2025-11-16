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

    Note right of Service: Service keeps looping,\naccepting new login, userinfo,\nand refresh requests
