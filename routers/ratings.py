# router for handling ratings
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import UserRating, Movie, User
from typing import List
from auth import get_current_user

# router setup with prefix for all rating endpoints
router = APIRouter(prefix="/ratings", tags=["Ratings"])

@router.get("/", response_model=List[dict])
def get_user_ratings(
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a list of all movies rated by the currently authenticated user
    """

    # query to join movies and ratings, filtered by the current user's id
    statement = select(Movie, UserRating.rating)\
    .where(Movie.id == UserRating.movie_id)\
    .where(UserRating.user_id == current_user.id)
    
    results = session.exec(statement).all()
    
    # merge the movie model and the rating value into a single dictionary
    movies_with_ratings = []
    for movie, rating_value in results:
        movie_dict = movie.model_dump()
        movie_dict["user_rating"] = rating_value 
        movies_with_ratings.append(movie_dict)
        
    return movies_with_ratings

@router.post("/")
def rate_movie(
    rating_data: UserRating, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Adds a new rating or updates an existing rating for a movie
    """

    # securely forces the rating to belong to the authenticated user
    rating_data.user_id = current_user.id 

    # checks if the user has already rated this specific movie
    statement = select(UserRating).where(
        UserRating.movie_id == rating_data.movie_id,
        UserRating.user_id == current_user.id
    )
    existing_rating = session.exec(statement).first()
    
    if existing_rating:
        # updates the existing rating value
        existing_rating.rating = rating_data.rating
        session.add(existing_rating)
    else:
        # inserts a new rating
        session.add(rating_data)
        
    session.commit()
    return {"ok": True}

@router.delete("/{movie_id}")
def delete_rating(
    movie_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Removes the current user's rating for a specific movie
    """

    # locates the specific rating in the database
    statement = select(UserRating).where(
        UserRating.movie_id == movie_id,
        UserRating.user_id == current_user.id
    )
    
    rating = session.exec(statement).first()
    
    # delete if found
    if rating:
        session.delete(rating)
        session.commit()
        return {"ok": True}
        
    raise HTTPException(status_code=404, detail="Rating not found")