import pytest
from models import Movie, User
from security import get_password_hash

def test_full_user_journey(client, session):
    """
    Simulates a complete flow: registration, login, rating, and recommendation
    """
    # seed database with required movies
    m1 = Movie(id=1, imdb_id="tt1", movie_id="101", title="The Matrix", year=1999, type="movie", poster="img.jpg")
    m2 = Movie(id=2, imdb_id="tt2", movie_id="102", title="Inception", year=2010, type="movie", poster="img.jpg")
    session.add_all([m1, m2])
    session.commit()

    # user registration
    reg_payload = {
        "nickname": "journey_user",
        "email": "journey@example.com",
        "password": "secure_password"
    }
    reg_response = client.post("/users/", json=reg_payload)
    assert reg_response.status_code == 200
    
    # user login to obtain real jwt
    login_payload = {
        "email": "journey@example.com",
        "password": "secure_password"
    }
    login_response = client.post("/token", json=login_payload)
    assert login_response.status_code == 200
    
    # extract token and setup headers
    token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # user rates a movie
    rating_payload = {"movie_id": 1, "rating": 5.0}
    rate_response = client.post("/ratings/", json=rating_payload, headers=auth_headers)
    assert rate_response.status_code == 200

    # verify the rating was saved and linked to the movie correctly
    list_response = client.get("/ratings/", headers=auth_headers)
    assert list_response.status_code == 200
    ratings_data = list_response.json()
    assert len(ratings_data) == 1
    assert ratings_data[0]["title"] == "The Matrix"
    assert ratings_data[0]["user_rating"] == 5.0

    # trigger EASE model to generate recommendations based on the new rating
    rec_response = client.get("/recommendations/", headers=auth_headers)
    assert rec_response.status_code == 200
    assert isinstance(rec_response.json(), list)

    # triggers SVD model to predict a specific rating for an unrated movie (Inception, id=2)
    rating_pred_response = client.get("/recommendations/2/rating", headers=auth_headers)
    assert rating_pred_response.status_code == 200
    pred_data = rating_pred_response.json()
    
    # verifies the prediction router returns the expected dictionary structure
    assert "predicted_rating" in pred_data
    assert isinstance(pred_data["predicted_rating"], float)

def test_cold_start_flow(client, session):
    """
    Simulates a new user requesting recommendations before rating anything
    """
    # seed a pre-registered user
    hashed_pwd = get_password_hash("cold_password")
    user = User(email="cold@example.com", nickname="cold_user", hashed_password=hashed_pwd)
    session.add(user)
    session.commit()

    # log in to get token
    login_response = client.post("/token", json={"email": "cold@example.com", "password": "cold_password"})
    token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # request recommendations without any prior ratings
    rec_response = client.get("/recommendations/", headers=auth_headers)
    
    # router should return an empty list without crashing the ml models
    assert rec_response.status_code == 200
    assert rec_response.json() == []

def test_rating_lifecycle(client, session):
    """
    Simulates a user adding, updating, and completely removing a rating
    """
    # seed database
    m1 = Movie(id=1, imdb_id="tt1", movie_id="101", title="The Matrix", year=1999, type="movie", poster="img.jpg")
    hashed_pwd = get_password_hash("life_password")
    user = User(email="lifecycle@example.com", nickname="tester", hashed_password=hashed_pwd)
    session.add_all([m1, user])
    session.commit()

    # authenticate
    login_response = client.post("/token", json={"email": "lifecycle@example.com", "password": "life_password"})
    token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # creates initial rating
    client.post("/ratings/", json={"movie_id": 1, "rating": 3.0}, headers=auth_headers)
    
    # updates the same rating
    client.post("/ratings/", json={"movie_id": 1, "rating": 5.0}, headers=auth_headers)
    
    # verifies it updated instead of duplicating
    list_response = client.get("/ratings/", headers=auth_headers)
    data = list_response.json()
    assert len(data) == 1
    assert data[0]["user_rating"] == 5.0

    # deletes the rating
    delete_response = client.delete("/ratings/1", headers=auth_headers)
    assert delete_response.status_code == 200

    # verifies the list is now empty
    final_list = client.get("/ratings/", headers=auth_headers)
    assert len(final_list.json()) == 0

def test_security_wall_rejection(client):
    """
    Simulates unauthorized access attempts to protected endpoints
    """
    # attempt to access ratings without a token
    ratings_response = client.get("/ratings/")
    assert ratings_response.status_code == 401
    
    # attempt to access recommendations without a token
    rec_response = client.get("/recommendations/")
    assert rec_response.status_code == 401

    # attempt to bypass with a malformed token
    bad_headers = {"Authorization": "Bearer not.a.real.jwt"}
    bad_response = client.get("/ratings/", headers=bad_headers)
    assert bad_response.status_code == 401