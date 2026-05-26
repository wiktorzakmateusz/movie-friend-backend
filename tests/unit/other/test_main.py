import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

def test_root_endpoint(client):
    """
    Tests the health check root endpoint
    """
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Movie Friend API"}

@patch("main.create_db_and_tables")
def test_lifespan_startup(mock_create_db):
    """
    Tests if db creation is called on app startup
    """
    with TestClient(app) as temp_client:
        pass
        
    # verifies the lifespan successfully triggered the database creation function
    mock_create_db.assert_called_once()

def test_cors_middleware_allowed_origin():
    """
    Tests if cors headers are returned for whitelisted origins
    """
    client = TestClient(app)
    
    # testing one of the origins from whitelist
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    }
    
    response = client.options("/", headers=headers)
    
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

def test_cors_middleware_rejected_origin():
    """
    Tests how cors handles requests from non-whitelisted domains
    """
    client = TestClient(app)
    
    headers = {
        "Origin": "https://malicious-website.com",
        "Access-Control-Request-Method": "GET"
    }
    
    response = client.options("/", headers=headers)
    
    assert response.status_code == 400
    assert response.text == "Disallowed CORS origin"