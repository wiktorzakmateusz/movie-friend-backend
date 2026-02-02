from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import Movie, MovieCreate, UserRating, User
from typing import List, Optional
from auth import get_current_user  # <--- 1. Import Auth

router = APIRouter(prefix="/movies", tags=["Movies"])

# --- 1. CREATE MOVIE (Unchanged) ---
@router.post("/", response_model=Movie)
def create_movie(movie: MovieCreate, session: Session = Depends(get_session)):
    statement = select(Movie).where(Movie.imdb_id == movie.imdb_id)
    if session.exec(statement).first():
        raise HTTPException(status_code=400, detail="Movie already exists")

    db_movie = Movie.model_validate(movie)
    session.add(db_movie)
    session.commit()
    session.refresh(db_movie)
    return db_movie

# --- 2. GET ALL MOVIES (Fixed) ---
@router.get("/", response_model=List[dict], response_model_by_alias=False)
def get_movies(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user) # <--- 2. Inject Current User
):
    statement = (
        select(Movie, UserRating.rating)
        .join(
            UserRating, 
            isouter=True, 
            # 3. CRITICAL FIX: Filter inside the JOIN
            # This ensures we only match ratings belonging to THIS user
            onclause=(
                (Movie.id == UserRating.movie_id) & 
                (UserRating.user_id == current_user.id)
            )
        ).limit(50)
    )
    results = session.exec(statement).all()
    
    movies_with_ratings = []
    for movie, rating in results:
        m = movie.model_dump()
        m["user_rating"] = rating 
        movies_with_ratings.append(m)
        
    return movies_with_ratings

# --- 3. SEARCH MOVIES (Fixed) ---
@router.get("/search", response_model=List[dict], response_model_by_alias=False)
def search_movies(
    title: Optional[str] = None,
    genre: Optional[str] = None,
    keyword: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user) # <--- Inject User
):
    statement = (
        select(Movie, UserRating.rating)
        .join(
            UserRating, 
            isouter=True, 
            onclause=(
                (Movie.id == UserRating.movie_id) & 
                (UserRating.user_id == current_user.id) # <--- Filter
            )
        ).limit(50)
    )
    
    if title:
        statement = statement.where(Movie.title.ilike(f"%{title}%"))
    
    if genre:
        statement = statement.where(Movie.genre.ilike(f"%{genre}%"))
        
    results = session.exec(statement).all()

    movies_with_ratings = []
    for movie, rating in results:
        m = movie.model_dump()
        m["user_rating"] = rating
        movies_with_ratings.append(m)
        
    return movies_with_ratings

# --- 4. GET SINGLE MOVIE (Fixed) ---
@router.get("/{movie_id}", response_model=dict, response_model_by_alias=False)
def get_movie(
    movie_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user) # <--- Inject User
):
    statement = (
        select(Movie, UserRating.rating)
        .where(Movie.id == movie_id)
        .join(
            UserRating, 
            isouter=True, 
            onclause=(
                (Movie.id == UserRating.movie_id) & 
                (UserRating.user_id == current_user.id) # <--- Filter
            )
        )
    )
    
    result = session.exec(statement).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    movie, rating = result
    
    movie_dict = movie.model_dump()
    movie_dict["user_rating"] = rating
    
    return movie_dict