from sqlmodel import Session, select
from typing import List, Dict
from models import UserRating, Movie
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_user_movies(session: Session, user_id: int) -> List[int]:
    """
    Fetches user ratings from DB (all, not ignored, and negative feedback seperately) and returns contiguous internal movie ids
    """

    # there are 4 kind of interactions
    # rating > 0 & ignore = False -> used for recommendation positive feedback (normal movies)
    # rating > 0 & ignore = True -> not used for recommendation positive feedback (ignored movies)
    # rating = -1 & ignore = False -> used for recommendation negative feedback (blocked movies)
    # rating = -1 & ignore = True -> not used for recommendation negative feedback (hidden movies)

    # user ratings to not be included in recommendations 
    # (all rated + ignored)
    statement = (
        select(Movie.id)
        .join(UserRating, Movie.id == UserRating.movie_id)
        .where(UserRating.user_id == user_id)
    )
    user_ratings = session.exec(statement).all()

    # user ratings used to train the model
    statement = (
        select(Movie.id)
        .join(UserRating, Movie.id == UserRating.movie_id)
        .where(UserRating.user_id == user_id)
        .where(UserRating.rating != -1)
        .where(UserRating.ignore == False)
    )
    user_ratings_without_ignored = session.exec(statement).all()

    # user negative feedback used to train the model
    statement = (
        select(Movie.id)
        .join(UserRating, Movie.id == UserRating.movie_id)
        .where(UserRating.user_id == user_id)
        .where(UserRating.rating == -1)
        .where(UserRating.ignore == False)
    )
    user_negative_feedback = session.exec(statement).all()

    return user_ratings, user_ratings_without_ignored, user_negative_feedback

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