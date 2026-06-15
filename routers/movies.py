# router for handling movies
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, delete, desc
from database import get_session
from models import Movie, MovieCreate, UserRating, User
from typing import List, Optional
from auth import get_current_user 

# router setup with prefix for all movie endpoints
router = APIRouter(prefix="/movies", tags=["Movies"])

@router.post("/", response_model=Movie)
def create_movie(movie: MovieCreate, session: Session = Depends(get_session)):
    """
    Adds a new movie to the database
    """

    # checks if movie with the same imdb_id already exists
    statement = select(Movie).where(Movie.imdb_id == movie.imdb_id)
    if session.exec(statement).first():
        raise HTTPException(status_code=400, detail="Movie already exists")

    # converts pydantic schema to sqlmodel instance and save
    db_movie = Movie.model_validate(movie)
    session.add(db_movie)
    session.commit()
    session.refresh(db_movie)
    return db_movie


@router.get("/search", response_model=List[dict], response_model_by_alias=False)
def search_movies(
    title: Optional[str] = None,
    genre: Optional[str] = None,
    keyword: Optional[str] = None,
    sort_by: Optional[str] = "popular",
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Searches for movies by title or genre and includes the current user's rating
    """

    # base query: selects movie and rating, using an outer join so unrated movies still appear
    statement = (
        select(Movie, UserRating.rating)
        .join(
            UserRating, 
            isouter=True, 
            onclause=(
                (Movie.id == UserRating.movie_id) & 
                (UserRating.user_id == current_user.id)
            )
        ).limit(50)
    )
    
    # applies filters dynamically if provided in the request
    if title:
        statement = statement.where(Movie.title.ilike(f"%{title}%"))
    if genre:
        statement = statement.where(Movie.genre.ilike(f"%{genre}%"))
    
    statement = statement.order_by(desc(Movie.imdb_rating))

    results = session.exec(statement).all()

    # merges the separated movie model and rating scalar into a single dictionary
    movies_with_ratings = []
    for movie, rating in results:
        m = movie.model_dump()
        m["user_rating"] = rating
        movies_with_ratings.append(m)
        
    return movies_with_ratings


@router.get("/{movie_id}", response_model=dict, response_model_by_alias=False)
def get_movie(
    movie_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a single movie by ID along with the current user's rating
    """

    # query specific movie and outer join to attach the user's specific rating
    statement = (
        select(Movie, UserRating.rating)
        .where(Movie.id == movie_id)
        .join(
            UserRating, 
            isouter=True, 
            onclause=(
                (Movie.id == UserRating.movie_id) & 
                (UserRating.user_id == current_user.id)
            )
        )
        .order_by(desc(Movie.imdb_votes))
    )
    
    result = session.exec(statement).first()
    
    # handles invalid movie id
    if not result:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    movie, rating = result
    
    # injects user's rating into the response dictionary
    movie_dict = movie.model_dump()
    movie_dict["user_rating"] = rating
    
    return movie_dict

# @router.delete("/")
# def delete_all_movies(
#     session: Session = Depends(get_session),
#     current_user: User = Depends(get_current_user) # TODO: admin only
# ):
#     """
#     WARNING: Deletes all movies in the database
#     """

#     statement = delete(Movie)
#     result = session.exec(statement)
#     session.commit()
    
#     return {"message": f"Successfully deleted {result.rowcount} movies."}


# TO DELETE
# @router.get("/", response_model=List[dict], response_model_by_alias=False)
# def get_movies(
#     session: Session = Depends(get_session),
#     current_user: User = Depends(get_current_user)
# ):
#     statement = (
#         select(Movie, UserRating.rating)
#         .join(
#             UserRating, 
#             isouter=True, 
#             onclause=(
#                 (Movie.id == UserRating.movie_id) & 
#                 (UserRating.user_id == current_user.id)
#             )
#         ).limit(50)
#     )
#     results = session.exec(statement).all()
    
#     movies_with_ratings = []
#     for movie, rating in results:
#         m = movie.model_dump()
#         m["user_rating"] = rating 
#         movies_with_ratings.append(m)
        
#     return movies_with_ratings

# @router.get("/ids", response_model=List[dict])
# def get_all_movie_ids(
#     session: Session = Depends(get_session),
# ):
#     statement = select(Movie.id, Movie.imdb_id)
#     results = session.exec(statement).all()
    
#     return [{"id": row.id, "imdb_id": row.imdb_id} for row in results]
