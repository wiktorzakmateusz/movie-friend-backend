# database scheme
from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import EmailStr
from sqlalchemy import Column, Integer, String, Float, Text, Boolean

# user base model
class UserBase(SQLModel):
    nickname: str
    email: EmailStr

# user input schema
class UserCreate(UserBase):
    password: str

# user database table
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model_id: Optional[int] # internal id for ML models
    hashed_password: str

# user output schema
class UserRead(UserBase):
    id: int

# login input
class LoginRequest(SQLModel):
    email: str
    password: str

# login output
class Token(SQLModel):
    access_token: str
    token_type: str

# movie base class
class MovieBase(SQLModel):
    id: int # internal id for ML models
    imdb_id: str = Field(alias="imdbID", unique=True, index=True) # Imdb id
    movie_id: str = Field(alias="movieID", unique=True, index=True) # MovieLens id
    title: str = Field(alias="Title", index=True)
    year: int = Field(alias="Year")
    type: str = Field(alias="Type")
    poster: str = Field(alias="Poster")
    
    runtime: Optional[str] = Field(default=None, alias="Runtime")
    genre: Optional[str] = Field(default=None, alias="Genre")
    director: Optional[str] = Field(default=None, alias="Director")
    writer: Optional[str] = Field(default=None, alias="Writer")
    actors: Optional[str] = Field(default=None, alias="Actors")
    plot: Optional[str] = Field(default=None, alias="Plot")
    country: Optional[str] = Field(default=None, alias="Country")
    awards: Optional[str] = Field(default=None, alias="Awards")
    
    imdb_rating: Optional[float] = Field(default=None, alias="imdbRating")
    imdb_votes: Optional[str] = Field(default=None, alias="imdbVotes") # to delete
    box_office: Optional[str] = Field(default=None, alias="BoxOffice")

    class Config:
        populate_by_name = True

# movie database table
class Movie(MovieBase, table=True):
    id: int = Field(sa_column=Column(Integer, primary_key=True, autoincrement=False))

# movie input
class MovieCreate(MovieBase):
    pass

# users' ratings database table
class UserRating(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    movie_id: int = Field(index=True, foreign_key="movie.id") # internal id for ML models
    rating: int 
    user_id: int = Field(foreign_key="user.id") # user table id column
