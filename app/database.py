"""SQLite connection setup using SQLAlchemy.

Reads DATABASE_URL from .env directly (config.py, which centralizes all
settings, is built in Block 1.3 -- this file will switch to importing
from it then).
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecommerce.db")

# check_same_thread=False is required for SQLite when the same connection
# pool is shared across FastAPI's request threads.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Parent class every ORM model (in models.py) inherits from."""


def get_db() -> Session:
    """Yield a database session and always close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
