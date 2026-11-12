import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from extras.app.config import settings
from extras.app.database.models import Base

# Engine configuration with thread safety for SQLite
connect_args = {"check_same_thread": False} if "sqlite" in settings.EXTRAS_DB_URL else {}
engine = create_engine(settings.EXTRAS_DB_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

# Auto-initialize on import so tables always exist even in test runners or direct TestClient instances
init_db()

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

