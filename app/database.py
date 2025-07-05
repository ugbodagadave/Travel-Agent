import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, JSON, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import redis

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

# Create the database engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Initialize Redis client
try:
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

def init_db():
    """
    Initializes the database by creating tables if they don't exist.
    """
    Base.metadata.create_all(bind=engine)

# To create the table initially, you might run this from a separate script
# or integrate it into your app's startup sequence. 