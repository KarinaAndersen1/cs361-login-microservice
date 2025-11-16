import pytest
from fastapi.testclient import TestClient

from login_service.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)
