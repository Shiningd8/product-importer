from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Creating the database engine
# Acts as the bridge between the Python code and PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Auto-reconnect if connection goes stale (because databases can be moody)
    pool_size=10,  # How many connections to keep warm and ready
    max_overflow=20,  # Extra connections for those busy moments
)

#  Session factory - creates database sessions on demand
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all our models.
# All models will inherit from this.
Base = declarative_base()


def get_db():
    """
    Database dependency generator for FastAPI routes.
    
    This is like a butler that opens a database session for you,
    makes sure everything is clean, and closes it when you're done.
    No mess, no fuss!
    """
    db = SessionLocal()
    try:
        yield db  # Hand over the session to whoever needs it
    finally:
        db.close()  # Always clean up after yourself - good manners!

