from sqlmodel import Session, select
from typing import List, Dict
from models import UserRating, Movie
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_user_movies(session: Session, user_id: int) -> List[int]:
    """
    Fetches user ratings from DB (ignored, and unignored seperately) and returns contiguous internal movie ids
    """
    statement = (
        select(Movie.id)
        .join(UserRating, Movie.id == UserRating.movie_id)
        .where(UserRating.user_id == user_id)
    )
    user_ratings = session.exec(statement).all()

    statement = (
        select(Movie.id)
        .join(UserRating, Movie.id == UserRating.movie_id)
        .where(UserRating.user_id == user_id)
        .where(UserRating.ignore == False)
    )
    user_ratings_without_ignored = session.exec(statement).all()

    return user_ratings, user_ratings_without_ignored

def get_movies_from_internal_ids(session: Session, ids: List[str]) -> List[Movie]:
    """
    Fetches full Movie objects from the DB based on a list of internal ids.
    Preserves the order of the recommendations.
    """
    if not ids:
        return []

    statement = select(Movie).where(Movie.id.in_(ids))
    movies = session.exec(statement).all()
    
    # helper
    movie_map = {m.id: m for m in movies}
    
    ordered_movies = []
    for id in ids:
        if id in movie_map:
            ordered_movies.append(movie_map[id])
            
    return ordered_movies