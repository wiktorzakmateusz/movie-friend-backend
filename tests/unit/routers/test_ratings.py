import pytest
from sqlmodel import select
from models import Movie, User, UserRating
from main import app
from auth import get_current_user

def test_get_user_ratings(auth_client, session, mock_user):
    """
    Tests retrieving user ratings with movie details, including the ignore flag
    """
    # inserts two movies
    movie1 = Movie(
        id=10, imdb_id="tt0133093", movie_id="2571", 
        title="The Matrix", year=1999, type="movie", poster="matrix.jpg"
    )
    movie2 = Movie(
        id=11, imdb_id="tt1375666", movie_id="27205", 
        title="Inception", year=2010, type="movie", poster="inception.jpg"
    )
    
    rating1 = UserRating(user_id=mock_user.id, movie_id=10, rating=9, ignore=False)
    rating2 = UserRating(user_id=mock_user.id, movie_id=11, rating=-1, ignore=True)
    
    session.add_all([movie1, movie2, rating1, rating2])
    session.commit()

    response = auth_client.get("/ratings/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    assert data[0]["title"] == "Inception"
    assert data[0]["user_rating"] == -1
    assert data[0]["ignore"] is True  # Verifying the ignore flag is passed!

    assert data[1]["title"] == "The Matrix"
    assert data[1]["user_rating"] == 9
    assert data[1]["ignore"] is False

def test_rate_movie_new(auth_client, session):
    """
    Tests adding a completely new rating
    """
    payload = {
        "movie_id": 10,
        "rating": 5.0,
        "user_id": 999 # should be securely overridden to 1 by the router
    }
    
    response = auth_client.post("/ratings/", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    
    # check if saved in db under correct user id
    statement = select(UserRating).where(UserRating.movie_id == 10)
    db_rating = session.exec(statement).first()
    
    assert db_rating is not None
    assert db_rating.rating == 5.0
    assert db_rating.user_id == 1

def test_rate_movie_update(auth_client, session, mock_user):
    """
    Tests updating an existing rating
    """
    # seed existing rating
    rating = UserRating(user_id=mock_user.id, movie_id=10, rating=3.0)
    session.add(rating)
    session.commit()

    payload = {
        "movie_id": 10,
        "rating": 4.0
    }
    
    response = auth_client.post("/ratings/", json=payload)
    
    assert response.status_code == 200
    
    db_rating = session.exec(select(UserRating).where(UserRating.movie_id == 10)).first()
    # verify rating was updated, not duplicated
    assert db_rating.rating == 4.0

def test_delete_rating_success(auth_client, session, mock_user):
    """
    Tests successful deletion of a rating
    """
    rating = UserRating(user_id=mock_user.id, movie_id=10, rating=4.0)
    session.add(rating)
    session.commit()

    response = auth_client.delete("/ratings/10")
    
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    
    remaining = session.exec(select(UserRating)).all()
    # verify db is completely empty
    assert len(remaining) == 0

def test_rate_movie_negative_feedback(auth_client, session):
    """
    Tests submitting a negative rating (-1) for hiding/blocking mechanics
    """
    payload = {
        "movie_id": 10,
        "rating": -1.0
    }
    
    response = auth_client.post("/ratings/", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    
    db_rating = session.exec(select(UserRating).where(UserRating.movie_id == 10)).first()
    assert db_rating is not None
    assert db_rating.rating == -1.0
    assert db_rating.ignore is False

def test_delete_rating_not_found(auth_client):
    """
    Tests 404 response when deleting non-existent rating
    """
    response = auth_client.delete("/ratings/999")
    
    assert response.status_code == 404
    assert response.json() == {"detail": "Rating not found"}

def test_ignore_movie_recommendation_success(auth_client, session, mock_user):
    """
    Tests successfully setting the ignore flag to True for an existing movie interaction
    """

    rating = UserRating(user_id=mock_user.id, movie_id=10, rating=4.0, ignore=False)
    session.add(rating)
    session.commit()

    payload = {"ignore": True}
    
    response = auth_client.patch("/ratings/10/ignore", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    
    statement = select(UserRating).where(UserRating.movie_id == 10)
    db_rating = session.exec(statement).first()
    
    assert db_rating.ignore is True

def test_unignore_movie_recommendation_success(auth_client, session, mock_user):
    """
    Tests successfully setting the ignore flag back to False (unignoring)
    """

    rating = UserRating(user_id=mock_user.id, movie_id=10, rating=3.5, ignore=True)
    session.add(rating)
    session.commit()

    payload = {"ignore": False}
    
    response = auth_client.patch("/ratings/10/ignore", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    
    statement = select(UserRating).where(UserRating.movie_id == 10)
    db_rating = session.exec(statement).first()
    
    assert db_rating.ignore is False

def test_ignore_movie_not_found(auth_client):
    """
    Tests that a 404 is raised if the user tries to ignore a movie they haven't interacted with
    """
    
    payload = {"ignore": True}
    
    response = auth_client.patch("/ratings/999/ignore", json=payload)
    
    assert response.status_code == 404
    assert response.json() == {
        "detail": "No watch history found for this movie. Cannot ignore."
    }