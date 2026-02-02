from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import UserRating, Movie, User
from typing import List
from auth import get_current_user

router = APIRouter(prefix="/ratings", tags=["Ratings"])

# 1. GET all rated movies (for My-Ratings page)
# We join Movie and UserRating to return the movie data + the user's specific rating
@router.get("/", response_model=List[dict])
def get_user_ratings(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Join Movie and Rating tables
    statement = select(Movie, UserRating.rating)\
    .where(Movie.id == UserRating.movie_id)\
    .where(UserRating.user_id == current_user.id)
    
    results = session.exec(statement).all()
    
    # Format the result to look like a Movie object but with 'user_rating' added
    movies_with_ratings = []
    for movie, rating_value in results:
        movie_dict = movie.model_dump()
        movie_dict["user_rating"] = rating_value # Inject the user rating
        movies_with_ratings.append(movie_dict)
        
    return movies_with_ratings

@router.post("/")
def rate_movie(
    rating_data: UserRating, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    rating_data.user_id = current_user.id 

    statement = select(UserRating).where(
        UserRating.movie_id == rating_data.movie_id,
        UserRating.user_id == current_user.id
    )
    existing_rating = session.exec(statement).first()
    
    if existing_rating:
        existing_rating.rating = rating_data.rating
        session.add(existing_rating)
    else:
        session.add(rating_data)
        
    session.commit()
    return {"ok": True}

# 3. DELETE a rating
@router.delete("/{movie_id}")
def delete_rating(
    movie_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    statement = select(UserRating).where(
        UserRating.movie_id == movie_id,
        UserRating.user_id == current_user.id
    )
    rating = session.exec(statement).first()
    
    if rating:
        session.delete(rating)
        session.commit()
        return {"ok": True}
        
    raise HTTPException(status_code=404, detail="Rating not found")