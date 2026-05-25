from unittest.mock import patch
from models import User

def test_login_success(client, session):

    test_user = User(email='user@example.com', hashed_password='fake_db_hash', nickname='test_user_123')
    session.add(test_user)
    session.commit()

    # mocking security functions
    with patch('routers.auth.verify_password', return_value=True), \
         patch('routers.auth.create_access_token', return_value='mocked_jwt_token'):
        
        response = client.post(
            '/token',
            json={'email': 'user@example.com', 'password': 'correct_password'}
        )

    assert response.status_code == 200
    assert response.json() == {
        'access_token': 'mocked_jwt_token', 
        'token_type': 'bearer'
    }

def test_login_wrong_password(client, session):

    test_user = User(email='user@example.com', hashed_password='fake_db_hash', nickname='test_user_123')
    session.add(test_user)
    session.commit()

    with patch('routers.auth.verify_password', return_value=False):
        
        response = client.post(
            '/token',
            json={'email': 'user@example.com', 'password': 'wrong_password'}
        )

    assert response.status_code == 401
    assert response.json() == {'detail': 'Incorrect email or password'}

def test_login_unregistered_email(client, session):

    response = client.post(
        '/token',
        json={'email': 'ghost@example.com', 'password': 'any_password'}
    )

    assert response.status_code == 401
    assert response.json() == {'detail': 'Incorrect email or password'}