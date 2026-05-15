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
    user_ratings = get_user_movies(session, current_user.id)

    # if none, returns empty list
    if not user_ratings:
        return [] 
    
    # getting recommended movies - a ndarray of movies internal ids
    recommended_movies_ids = ease.predict_new_user(user_ratings, k=20)

    # returns list of movie objects
    recommended_movies = get_movies_from_internal_ids(session, recommended_movies_ids.tolist())

    return [movie.model_dump() for movie in recommended_movies] # converting to standard py dict

@router.get("/{current_item}/")
def get_ratings(
    current_item: int,
    current_user: User = Depends(get_current_user)
):
    """
    Predicts rating for an users & item pair
    """

    # getting recommendation
    rating = svd.estimate(current_user.model_id, current_item)

    # scaling to the 1-10 scale
    rating *= 2
    rating = min(10, rating)
    rating = max(1, rating)

    return {"predicted_rating": round(rating, 1)}