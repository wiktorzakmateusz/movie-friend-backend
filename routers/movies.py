from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import Movie, MovieCreate
from typing import List

router = APIRouter(prefix="/movies", tags=["Movies"])

@router.post("/", response_model=Movie)
def create_movie(movie: MovieCreate, session: Session = Depends(get_session)):
    # Check for duplicates
    statement = select(Movie).where(Movie.imdb_id == movie.imdb_id)
    if session.exec(statement).first():
        raise HTTPException(status_code=400, detail="Movie already exists")

    # Convert Input Schema -> Database Table Model
    db_movie = Movie.model_validate(movie)
    
    session.add(db_movie)
    session.commit()
    session.refresh(db_movie)
    return db_movie

@router.get("/", response_model=List[Movie], response_model_by_alias=False)
def get_movies(session: Session = Depends(get_session)):
    return session.exec(select(Movie)).all()