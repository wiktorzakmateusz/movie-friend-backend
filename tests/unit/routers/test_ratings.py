import pytest
from sqlmodel import select
from models import Movie, User, UserRating
from main import app
from auth import get_current_user

def test_get_user_ratings(auth_client, session, mock_user):
    """
    Tests retrieving user ratings with movie details
    """
    # insert required movie fields
    movie = Movie(
        id=10, 
        imdb_id="tt0133093", 
        movie_id="2571", 
        title="The Matrix", 
        year=1999, 
        type="movie", 
        poster="https://example.com/matrix.jpg"
    )
    # mock user has id 1
    rating = UserRating(user_id=mock_user.id, movie_id=10, rating=9)
    
    session.add(movie)
    session.add(rating)
    session.commit()

    response = auth_client.get("/ratings/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "The Matrix"
    assert data[0]["user_rating"] == 9

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

def test_delete_rating_not_found(auth_client):
    """
    Tests 404 response when deleting non-existent rating
    """
    response = auth_client.delete("/ratings/999")
    
    assert response.status_code == 404
    assert response.json() == {"detail": "Rating not found"}