import pytest
from models import Movie, User, UserRating
from main import app
from auth import get_current_user

def test_create_movie_success(client, session):
    """
    Tests successful movie creation
    """
    payload = {
        "id": 1,
        "imdb_id": "tt0816692",
        "movie_id": "109487",
        "title": "Interstellar",
        "year": 2014,
        "type": "movie",
        "poster": "https://example.com/interstellar.jpg"
    }
    
    response = client.post("/movies/", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["Title"] == "Interstellar"
    assert data["movieID"] == "109487"

def test_create_movie_duplicate_fails(client, session):
    """
    Tests rejection of duplicate movie
    """
    movie = Movie(
        id=2, 
        imdb_id="tt1160419", 
        movie_id="4321", 
        title="Dune", 
        year=2021, 
        type="movie", 
        poster="https://example.com/dune.jpg"
    )
    session.add(movie)
    session.commit()

    # Attempting to insert a movie with the exact same imdb_id
    response = client.post(
        "/movies/", 
        json={
            "id": 3, 
            "imdb_id": "tt1160419", 
            "movie_id": "9876", 
            "title": "Dune 2", 
            "year": 2024, 
            "type": "movie", 
            "poster": "https://example.com/dune2.jpg"
        }
    )
    
    assert response.status_code == 400
    assert response.json() == {"detail": "Movie already exists"}

def test_get_movie_success_with_rating(auth_client, session, mock_user):
    """
    Tests retrieving a movie with user rating
    """
    movie = Movie(
        id=10, 
        imdb_id="tt0133093", 
        movie_id="2571", 
        title="The Matrix", 
        year=1999, 
        type="movie", 
        poster="https://example.com/matrix.jpg"
    )
    rating = UserRating(user_id=mock_user.id, movie_id=10, rating=5.0)
    
    session.add(movie)
    session.add(rating)
    session.commit()

    response = auth_client.get("/movies/10")
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "The Matrix"
    assert data["user_rating"] == 5.0 

def test_get_movie_not_found(auth_client):
    """
    Tests 404 response for nonexistent movie
    """
    response = auth_client.get("/movies/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Movie not found"}

def test_search_movies_filtering(auth_client, session):
    """
    Tests searching movies by title and genre
    """
    movies = [
        Movie(id=1, imdb_id="tt1", movie_id="m1", title="Batman Begins", year=2005, type="movie", poster="img1.jpg"),
        Movie(id=2, imdb_id="tt2", movie_id="m2", title="The Dark Knight", year=2008, type="movie", poster="img2.jpg"),
        Movie(id=3, imdb_id="tt3", movie_id="m3", title="Spirited Away", year=2001, type="movie", poster="img3.jpg")
    ]
    session.add_all(movies)
    session.commit()

    response_title = auth_client.get("/movies/search?title=dark")
    assert response_title.status_code == 200
    assert len(response_title.json()) == 1
    assert response_title.json()[0]["title"] == "The Dark Knight"


def test_delete_all_movies(auth_client, session):
    """
    Tests deletion of all movies
    """
    movies = [
        Movie(id=10, imdb_id="tt10", movie_id="m10", title="Movie 1", year=2020, type="movie", poster="img10.jpg"),
        Movie(id=11, imdb_id="tt11", movie_id="m11", title="Movie 2", year=2021, type="movie", poster="img11.jpg")
    ]
    session.add_all(movies)
    session.commit()

    response = auth_client.delete("/movies/")
    
    assert response.status_code == 200
    assert response.json() == {"message": "Successfully deleted 2 movies."}
    
    from sqlmodel import select
    remaining_movies = session.exec(select(Movie)).all()
    assert len(remaining_movies) == 0