"""SQLite connection setup using SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# check_same_thread=False is required for SQLite when the same connection
# pool is shared across FastAPI's request threads.
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})

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
