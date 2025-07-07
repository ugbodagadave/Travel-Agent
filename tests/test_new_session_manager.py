import pytest
import json
from app.new_session_manager import save_session, load_session
from app.database import Conversation, SessionLocal

def test_save_session(db_session, mock_redis):
    """
    Tests that `save_session` correctly saves data to both the database and Redis cache.
    """
    user_id = "test_user_save"
    state = "BOOKING_COMPLETE"
    history = [("user", "thanks")]
    offers = ["offer3"]

    save_session(user_id, state, history, offers)

    # Verify data in Redis
    cached_data = mock_redis.get(user_id)
    assert cached_data is not None
    session_data = json.loads(cached_data)
    assert session_data['state'] == state
    assert session_data['conversation_history'] == [list(item) for item in history]
    assert session_data['flight_offers'] == offers

    # Verify data in Database
    db_convo = db_session.query(Conversation).filter(Conversation.user_id == user_id).first()
    assert db_convo is not None
    assert db_convo.history['state'] == state
    assert db_convo.history['conversation_history'] == [list(item) for item in history]

def test_load_session_from_db_and_caches_it(db_session, mock_redis):
    """
    Tests that a session is loaded from the DB when not in cache,
    and is then cached in Redis.
    """
    user_id = "test_user_db_load"
    session_data = {
        "state": "AWAITING_PAYMENT",
        "conversation_history": [["user", "book it"]],
        "flight_offers": ["offer2"]
    }
    # Pre-populate the database
    db_convo = Conversation(user_id=user_id, history=session_data)
    db_session.add(db_convo)
    db_session.commit()

    # Ensure cache is empty for this user
    assert mock_redis.get(user_id) is None

    # Load the session
    state, history, offers = load_session(user_id)

    # Verify loaded data is correct
    assert state == "AWAITING_PAYMENT"
    assert history == [["user", "book it"]]
    assert offers == ["offer2"]

    # Verify that the session is now in the cache
    cached_data = mock_redis.get(user_id)
    assert cached_data is not None
    assert json.loads(cached_data)['state'] == "AWAITING_PAYMENT"

def test_load_session_from_cache(db_session, mock_redis):
    """
    Tests that a session is loaded from the cache and the DB is not hit.
    """
    user_id = "test_user_cache_load"
    # Pre-populate the cache
    session_data = {
        "state": "IN_CACHE",
        "conversation_history": [["user", "cached?"]],
        "flight_offers": ["cached_offer"]
    }
    mock_redis.set(user_id, json.dumps(session_data))

    # Load the session
    state, history, offers = load_session(user_id)

    # Verify loaded data is correct
    assert state == "IN_CACHE"
    assert history == [["user", "cached?"]]
    assert offers == ["cached_offer"]

    # Verify that the database was not queried
    db_convo = db_session.query(Conversation).filter(Conversation.user_id == user_id).first()
    assert db_convo is None

def test_load_session_not_found(db_session, mock_redis):
    """
    Tests that a new, default session is returned when the user is not found
    in either the cache or the database.
    """
    user_id = "test_user_not_found"

    # Ensure cache and DB are empty for this user
    assert mock_redis.get(user_id) is None
    assert db_session.query(Conversation).filter(Conversation.user_id == user_id).first() is None

    state, history, offers = load_session(user_id)

    assert state == "GATHERING_INFO"
    assert history == []
    assert offers == [] 