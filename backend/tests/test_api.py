from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

@pytest.fixture
def test_db():
    # Setup test database
    conn = sqlite3.connect(':memory:')
    yield conn
    conn.close()

def test_analyze_endpoint():
    response = client.post(
        "/analyze",
        json={"target": "example.com", "scan_depth": "normal"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_execute_endpoint():
    test_commands = ["nmap -sV example.com"]
    response = client.post(
        "/execute/test_playbook",
        json=test_commands
    )
    assert response.status_code == 200
    assert "output" in response.json()
