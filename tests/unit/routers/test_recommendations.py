import pytest
import numpy as np
from unittest.mock import patch
from models import Movie, User
from main import app
from auth import get_current_user

@patch("routers.recommendations.get_user_movies")
def test_get_recommendations_empty_history(mock_get_movies, auth_client):
    """
    Tests returning empty list when user has no ratings
    """
    # simulates user having no watched movies
    mock_get_movies.return_value = ([], [], [])
    
    response = auth_client.get("/recommendations/")
    
    assert response.status_code == 200
    assert response.json() == []

@patch("routers.recommendations.get_user_movies")
@patch("routers.recommendations.ease.predict_new_user")
@patch("routers.recommendations.get_movies_from_internal_ids")
def test_get_recommendations_success(mock_get_movie_objects, mock_ease_predict, mock_get_user_movies, auth_client):
    """
    Tests successful movie recommendations list
    """
    # simulates user watch history
    mock_history = [{"movie_id": 10, "rating": 5.0}, {"movie_id": 11, "rating": 4.0}]
    mock_negative = [{"movie_id": 12, "rating": -1.0}]
    mock_get_user_movies.return_value = (mock_history, mock_history, mock_negative)
    
    # simulates ease returning an array of internal ids
    mock_ease_predict.return_value = np.array([101, 102])
    
    # simulates fetching movie objects from the db
    mock_get_movie_objects.return_value = [
        Movie(id=101, imdb_id="tt1", movie_id="101", title="Rec Movie 1", year=2020, type="movie", poster="img1.jpg"),
        Movie(id=102, imdb_id="tt2", movie_id="102", title="Rec Movie 2", year=2021, type="movie", poster="img2.jpg")
    ]
    
    response = auth_client.get("/recommendations/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Rec Movie 1"
    
    # verifies ease was called with the k=20 parameter from router
    mock_ease_predict.assert_called_once_with(
        mock_history, mock_history, mock_negative, negative_weight=0.5, k=20
    )

@patch("routers.recommendations.svd")
def test_get_ratings_standard(mock_svd, auth_client):
    """
    Tests normal svd rating prediction scaling
    """
    # simulates svd returning a raw 1-5 rating
    mock_svd.estimate.return_value = 3.6
    
    response = auth_client.get("/recommendations/99/rating")
    
    assert response.status_code == 200
    assert response.json() == {"predicted_rating": 7.2}
    
    # verifies svd was called with correct user model_id (42) and item_id (99)
    mock_svd.estimate.assert_called_once_with(42, 99)

@patch("routers.recommendations.svd")
def test_get_ratings_boundaries(mock_svd, auth_client):
    """
    Tests max and min rating boundaries
    """
    # tests maximum boundary (should cap at 10)
    mock_svd.estimate.return_value = 6.0 
    response_high = auth_client.get("/recommendations/123/rating")
    assert response_high.json() == {"predicted_rating": 10.0}
    
    # tests minimum boundary (should floor at 1)
    mock_svd.estimate.return_value = 0.2 
    response_low = auth_client.get("/recommendations/123/rating")
    assert response_low.json() == {"predicted_rating": 1.0}

@patch("routers.recommendations.ease.predict_new_user")
@patch("routers.recommendations.get_movies_from_internal_ids")
def test_get_similar_movies_success(mock_get_movie_objects, mock_ease_predict, auth_client):
    """
    Tests successful retrieval of similar movies
    """
    target_movie_id = 99
    
    # simulates ease returning an array of internal ids for similar movies
    mock_ease_predict.return_value = np.array([201, 202, 203])
    
    # simulates fetching movie objects from the db
    mock_get_movie_objects.return_value = [
        Movie(id=1, imdb_id="tt1", movie_id="201", title="Similar Movie 1", year=2020, type="movie", poster="img1.jpg"),
        Movie(id=2, imdb_id="tt2", movie_id="202", title="Similar Movie 2", year=2021, type="movie", poster="img2.jpg"),
        Movie(id=3, imdb_id="tt3", movie_id="203", title="Similar Movie 3", year=2022, type="movie", poster="img3.jpg")
    ]
    
    response = auth_client.get(f"/recommendations/{target_movie_id}/similar_movies")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["title"] == "Similar Movie 1"
    
    # verifies ease was called with the single item list and k=5
    mock_ease_predict.assert_called_once_with([target_movie_id], [target_movie_id], [], k=5)
    
    # verifies the db fetch was called with the resulting list from ease
    mock_get_movie_objects.assert_called_once()
    args, _ = mock_get_movie_objects.call_args
    assert args[1] == [201, 202, 203] 


@patch("routers.recommendations.get_user_movies")
def test_explain_recommendation_empty_history(mock_get_movies, auth_client):
    """
    Tests returning an empty list when the user has no usable watch history
    (or all ignored)
    """
    mock_get_movies.return_value = ([], [], [])
    
    response = auth_client.get("/recommendations/99/explain")
    
    assert response.status_code == 200
    assert response.json() == []

@patch("routers.recommendations.get_user_movies")
@patch("routers.recommendations.ease.explain_recommendation")
@patch("routers.recommendations.get_movies_from_internal_ids")
def test_explain_recommendation_success(
    mock_get_movie_objects, 
    mock_ease_explain, 
    mock_get_user_movies, 
    auth_client
):
    """
    Tests successfully returning an explanation of a movie recommendation
    """
    # simulates a user watch history tuple: (full_history, unignored_history)
    mock_history = [{"movie_id": 10, "rating": 5.0}, {"movie_id": 11, "rating": 4.0}]
    mock_get_user_movies.return_value = (mock_history, mock_history, [])
    
    # simulates ease returning internal ids and their raw calculation weights
    mock_ease_explain.return_value = ([101, 102], [0.85472, 0.42119])
    
    # simulates fetching movie objects from the db
    mock_get_movie_objects.return_value = [
        Movie(id=1, imdb_id="tt1", movie_id="101", title="Explanation Movie 1", year=2020, type="movie", poster="img1.jpg"),
        Movie(id=2, imdb_id="tt2", movie_id="102", title="Explanation Movie 2", year=2021, type="movie", poster="img2.jpg")
    ]
    
    target_item = 99
    response = auth_client.get(f"/recommendations/{target_item}/explain")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    
    assert data[0]["weight"] == 0.855 
    assert data[1]["weight"] == 0.421
    
    assert data[0]["movie"]["title"] == "Explanation Movie 1"
    assert data[1]["movie"]["title"] == "Explanation Movie 2"
    
    mock_ease_explain.assert_called_once_with(mock_history, target_item, top_n=3)
    
    mock_get_movie_objects.assert_called_once()
    args, _ = mock_get_movie_objects.call_args
    assert args[1] == [101, 102]