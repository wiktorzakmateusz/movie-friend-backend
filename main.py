from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_db_and_tables

from routers import users, auth, movies

app = FastAPI()

# Middleware Setup
origins = ["http://localhost:3000", "https://movie-friend.vercel.app"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(movies.router)

@app.get("/")
def root():
    return {"message": "Welcome to Movie Friend API"}