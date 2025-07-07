import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
import redis

# Load environment variables from .env file
load_dotenv()

# --- Global variables for database connection ---
engine = None
SessionLocal = None
Base = declarative_base()

def init_db(db_url=None):
    """
    Initializes the database by creating an engine and tables.
    Can be called with a specific db_url for testing purposes.
    """
    global engine, SessionLocal
    
    if db_url is None:
        db_url = os.getenv("DATABASE_URL")

    if engine is None or str(engine.url) != db_url:
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)

# Initialize Redis client
try:
    REDIS_URL = os.getenv("REDIS_URL")
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    print("Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"Could not connect to Redis: {e}")
    redis_client = None

# Define the Conversation model which corresponds to our database table
class Conversation(Base):
    __tablename__ = "conversations"

    user_id = Column(String, primary_key=True, index=True)
    history = Column(JSON) 