import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Store the database in the MessageLock project folder, unless
# MESSAGELOCK_DATABASE_PATH points somewhere else (the tests use this).
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(
    os.environ.get("MESSAGELOCK_DATABASE_PATH", BASE_DIR / "messagelock.db"))
DATABASE_URL = f"sqlite:///{DATABASE_PATH.resolve().as_posix()}"

class Base(DeclarativeBase):
    pass

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, _connection_record):
    """SQLite ignores foreign keys unless they are turned on per connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

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
    import models

    Base.metadata.create_all(bind=engine)