from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import EmailStr
from sqlalchemy import Column, Integer, String, Float, Text, Boolean

# Base Model (Shared properties)
class UserBase(SQLModel):
    nickname: str
    email: EmailStr

# Input Schema (What the user sends during sign up)
class UserCreate(UserBase):
    password: str

# Database Table (What is actually stored)
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str

# Output Schema (What is send back - NO password)
class UserRead(UserBase):
    id: int

# Input: What Next.js sends to /token
class LoginRequest(SQLModel):
    email: str
    password: str

# Output: What we send back to Next.js
class Token(SQLModel):
    access_token: str
    token_type: str

# Base class shares fields between the Database Table and Input Schema
class MovieBase(SQLModel):
    imdb_id: str = Field(alias="imdbID", unique=True, index=True)
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
    imdb_votes: Optional[str] = Field(default=None, alias="imdbVotes")
    box_office: Optional[str] = Field(default=None, alias="BoxOffice")

    class Config:
        populate_by_name = True

# The actual table in the database
class Movie(MovieBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

# The schema for validating input (used in your POST request)
class MovieCreate(MovieBase):
    pass

class UserRating(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    movie_id: int = Field(index=True)
    rating: int
    user_id: int = Field(foreign_key="user.id")