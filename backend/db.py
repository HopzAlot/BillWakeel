
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

# Project root is the parent of the backend directory.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{(DATA_DIR / 'billwakeel.db').as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """Provide a database session and close it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables and apply lightweight SQLite schema updates."""
    from models import db_models

    Base.metadata.create_all(bind=engine)

    columns = {
        column["name"]
        for column in inspect(engine).get_columns("bills")
    }

    if "warnings" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE bills "
                    "ADD COLUMN warnings JSON NOT NULL DEFAULT '[]'"
                )
            )
