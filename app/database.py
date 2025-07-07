import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, JSON
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from .env file
load_dotenv()

# --- Database Connection ---
engine = None
SessionLocal = None
Base = declarative_base()

def init_db(db_url=None):
    """
    Initializes the database connection and session maker.
    This function should be called once at application startup.
    If db_url is provided, it will be used; otherwise, it falls back to the DATABASE_URL environment variable.
    """
    global engine, SessionLocal
    
    if db_url is None:
        db_url = os.getenv("DATABASE_URL")

    # The engine and SessionLocal are created only if they haven't been already.
    # This check prevents re-initialization, which is important for testing.
    if engine is None:
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)

# Define the Conversation model which corresponds to our database table
class Conversation(Base):
    __tablename__ = "conversations"

    user_id = Column(String, primary_key=True, index=True)
    history = Column(JSON) 