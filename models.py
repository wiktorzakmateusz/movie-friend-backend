from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import EmailStr

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