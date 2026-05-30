# movie-friend-backend
Backend for movie friend app

to run locally: uvicorn main:app --reload  

to check db:
sqlite3 database.db
SELECT id, movie_id, ignore FROM userrating LIMIT 10; // example
.quit
