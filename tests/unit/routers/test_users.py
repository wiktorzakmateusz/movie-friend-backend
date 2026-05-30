import pytest
from unittest.mock import patch
from sqlmodel import select
from models import User
from main import app

def test_create_user_success(client, session):
    """
    Tests successful user registration
    """
    payload = {
        "nickname": "new_tester",
        "email": "new@example.com",
        "password": "secure_password"
    }

    # bypasses the slow hashing algorithm
    with patch("routers.users.get_password_hash", return_value="mocked_hash"):
        response = client.post("/users/", json=payload)
        
    assert response.status_code == 200
    data = response.json()
    
    assert data["email"] == "new@example.com"
    assert data["nickname"] == "new_tester"
    # ensures password is not returned in the read schema
    assert "password" not in data
    assert "hashed_password" not in data

    # verifies user was actually saved to database
    db_user = session.exec(select(User).where(User.email == "new@example.com")).first()
    assert db_user is not None
    assert db_user.hashed_password == "mocked_hash"

def test_create_user_duplicate_email(client, session):
    """
    Tests rejection when email is already in use
    """
    # seeds existing user
    existing_user = User(
        email="taken@example.com", 
        nickname="first_user", 
        hashed_password="old_hash"
    )
    session.add(existing_user)
    session.commit()

    payload = {
        "nickname": "second_user",
        "email": "taken@example.com",
        "password": "new_password"
    }

    response = client.post("/users/", json=payload)
    
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}

def test_create_user_missing_fields(client):
    """
    Tests pydantic validation for missing required fields
    """
    # payload missing the required 'password' field
    payload = {
        "nickname": "incomplete_user",
        "email": "incomplete@example.com"
    }

    response = client.post("/users/", json=payload)
    
    # pydantic should automatically reject this with a 422 unprocessable entity
    assert response.status_code == 422