from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Store the database in the MessageLock project folder.
BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{(BASE_DIR / 'messagelock.db').as_posix()}"

class Base(DeclarativeBase):
    pass

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

def get_database():
    """Provide a database session to API endpoints."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create database tables that do not already exist."""
    import models  # Register the database models

    Base.metadata.create_all(bind=engine)