# router for handling recommendations
import os
from fastapi import APIRouter, Depends, HTTPException, Depends, Request
from sqlmodel import Session
from typing import List, Dict, Any

from database import get_session          
from auth import get_current_user     
from models import User, Movie       
from ml.models_code.EASE import EASE 
from ml.utils.utils import get_user_movies, get_movies_from_internal_ids
# import logging
from ml.models_code.svd import SVD
from ml.models_code.EASE import EASE

# router setup with prefix for all recommendation endpoints
router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"]
)

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# model initialisation and loading
svd = SVD.load('ml/models/SVD.npz')
ease = EASE()
ease.load_model('ml/models/B_ease.npz')

@router.get("/")
def get_recommendations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Generates personalized movie recommendations for the current user.
    """

    # returns a list of movies watched
    user_history, user_history_without_ignored, negative_feedback = get_user_movies(session, current_user.id)

    # if none, returns empty list
    if not user_history_without_ignored:
        return []
    
    # getting recommended movies - a ndarray of movies internal ids
    recommended_movies_ids = ease.predict_new_user(user_history, user_history_without_ignored, 
                                                   negative_feedback, negative_weight=0.5, k=20)

    # returns list of movie objects
    recommended_movies = get_movies_from_internal_ids(session, recommended_movies_ids.tolist())

    return [movie.model_dump() for movie in recommended_movies] # converting to standard py dict

@router.get("/{current_item}/rating")
def get_ratings(
    current_item: int,
    current_user: User = Depends(get_current_user)
):
    """
    Predicts rating for an user & item pair
    """

    # Cython strictly requires an integer. If the user is new (model_id is None),
    # -1 is passed so the SVD model cleanly falls back to the global mean
    safe_user_id = current_user.model_id if current_user.model_id is not None else -1

    # getting recommendation
    rating = svd.estimate(safe_user_id, current_item)

    # scaling to the 1-10 scale
    rating *= 2
    rating = min(10, rating)
    rating = max(1, rating)

    return {"predicted_rating": round(rating, 1)}

@router.get("/{current_item}/similar_movies")
def get_similar_movies(
    current_item: int,
    session: Session = Depends(get_session)
):
    """
    Predicts similar movies for an user & item pair
    """
    
    # getting similar movies is equivalent to recommending movies to the user 
    # with history of that specific movie

    # getting similar movies - a ndarray of movies internal ids
    similar_movies_ids = ease.predict_new_user([current_item], [current_item], [], k=5)

    # returns list of movie objects
    similar_movies = get_movies_from_internal_ids(session, similar_movies_ids.tolist())

    return [movie.model_dump() for movie in similar_movies] # converting to standard py dict

@router.get("/{current_item}/explain")
def explain_recommendation(
    current_item: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Explains why a certain movie has been recommended based on user history
    """
    
    # returns a list of movies watched
    user_history, user_history_without_ignored, negative_feedback = get_user_movies(session, current_user.id)

    # if none, returns empty list
    if not user_history_without_ignored:
        return []

    # getting predictors and their weights - a list of movies internal ids and a list of weights
    predictors_ids, weights = ease.explain_recommendation(user_history_without_ignored, current_item, top_n=3)

    # returns list of movie objects
    predictors = get_movies_from_internal_ids(session, predictors_ids)

    return [
        {
            "movie": movie.model_dump(), 
            "weight": round(float(weight), 3)
        } 
        for movie, weight in zip(predictors, weights)
    ]