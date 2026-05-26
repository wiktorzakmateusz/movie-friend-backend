import pytest
from datetime import timedelta
from jose import jwt
from fastapi import HTTPException
from models import User
from auth import (
    create_access_token, 
    get_current_user, 
    SECRET_KEY, 
    ALGORITHM
)

def test_create_access_token():
    """
    Tests generating a valid jwt
    """
    data = {"sub": "test@example.com"}
    token = create_access_token(data)
    
    # decodes the token to verify contents
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload.get("sub") == "test@example.com"
    assert "exp" in payload

def test_create_access_token_custom_expire():
    """
    Tests custom expiration time
    """
    data = {"sub": "expire@example.com"}
    expires = timedelta(minutes=5)
    token = create_access_token(data, expires_delta=expires)
    
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload.get("sub") == "expire@example.com"

def test_get_current_user_success(session, mock_user):
    """
    Tests successfully retrieving user from valid token
    """
    token = create_access_token({"sub": mock_user.email})
    
    user = get_current_user(token=token, session=session)
    assert user.email == mock_user.email
    assert user.id == mock_user.id

def test_get_current_user_missing_token(session):
    """
    Tests missing token exception
    """
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=None, session=session)
        
    assert exc_info.value.status_code == 401

def test_get_current_user_invalid_token(session):
    """
    Tests malformed token rejection
    """
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="not.a.real.token", session=session)
        
    assert exc_info.value.status_code == 401

def test_get_current_user_expired_token(session):
    """
    Tests expired token rejection
    """
    # creates a token that expired 10 minutes ago
    expires = timedelta(minutes=-10)
    token = create_access_token({"sub": "test@example.com"}, expires_delta=expires)
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=token, session=session)
        
    assert exc_info.value.status_code == 401

def test_get_current_user_not_found(session):
    """
    Tests valid token but user missing from db
    """
    token = create_access_token({"sub": "ghost@example.com"})
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=token, session=session)
        
    assert exc_info.value.status_code == 401