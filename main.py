# main.py - entry point for entire API 
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import User, Movie, UserRating
from database import create_db_and_tables
from contextlib import asynccontextmanager
from routers import users, auth, movies, ratings, recommendations

# logger instance
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# runs code before the app starts taking requests
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # creates database tables if they don't exist yet
        create_db_and_tables()
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
    yield

# initializes the main FastAPI application instance
app = FastAPI(lifespan=lifespan)

# allowing frontend requests
origins = ["http://localhost:3000", "https://movie-friend.vercel.app"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # whitelist of domains
    allow_credentials=True, # allows cookies / authorization headers
    allow_methods=["*"], # allows all HTTP requests
    allow_headers=["*"], # allows all headers
)

# routers inclusions
app.include_router(users.router) # user handling
app.include_router(auth.router) # authentication handling
app.include_router(movies.router) # movies handling
app.include_router(ratings.router) # ratings handling
app.include_router(recommendations.router) # recommendations handling

# health-check route
@app.get("/")
def root():
    return {"message": "Welcome to Movie Friend API"}