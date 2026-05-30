import pytest
from sqlmodel import select
from models import Movie, User, UserRating
from ml.utils.utils import get_user_movies, get_movies_from_internal_ids

def test_get_user_movies_success(session, seed_data):
    """
    Tests if correct movie ids are fetched for a specific user
    """
    # user 1 should only have rated movie ids 10 and 20
    result, result_without_ignored = get_user_movies(session, user_id=1)
    
    assert len(result) == 2
    assert len(result_without_ignored) == 2
    assert 10 in result
    assert 20 in result
    assert 30 not in result # user 2's rating should be excluded

def test_get_user_movies_with_ignored(session, seed_data):
    """
    Tests if ignored movies are filtered correctly from the second list
    """
    # manually sets movie 10 as ignored for user 1
    statement = select(UserRating).where(UserRating.user_id == 1, UserRating.movie_id == 10)
    rating = session.exec(statement).first()
    rating.ignore = True
    session.add(rating)
    session.commit()

    result, result_without_ignored = get_user_movies(session, user_id=1)
    
    # full history still has both
    assert len(result) == 2 
    assert 10 in result
    
    # unignored history should drop movie 10
    assert len(result_without_ignored) == 1 
    assert 10 not in result_without_ignored
    assert 20 in result_without_ignored

def test_get_user_movies_empty(session):
    """
    Tests behavior for a user with no ratings
    """
    result, result_without_ignored = get_user_movies(session, user_id=999)
    assert result == []
    assert result_without_ignored == []

def test_get_movies_from_internal_ids_order(session, seed_data):
    """
    Tests if movies are fetched and returned in the exact requested order
    """
    # request movies out of natural database order
    requested_ids = [30, 10, 20]
    
    result = get_movies_from_internal_ids(session, requested_ids)
    
    assert len(result) == 3
    # verifies the order was strictly preserved
    assert result[0].id == 30
    assert result[1].id == 10
    assert result[2].id == 20

def test_get_movies_from_internal_ids_empty(session):
    """
    Tests early exit when provided an empty list
    """
    result = get_movies_from_internal_ids(session, [])
    assert result == []

def test_get_movies_from_internal_ids_partial_match(session, seed_data):
    """
    Tests handling of non-existent ids in the requested list
    """
    # 999 does not exist in the database
    requested_ids = [10, 999]
    
    result = get_movies_from_internal_ids(session, requested_ids)
    
    # should only return the valid movie and skip the missing one
    assert len(result) == 1
    assert result[0].id == 10