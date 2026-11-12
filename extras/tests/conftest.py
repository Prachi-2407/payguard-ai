import os
import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from extras.app.database.models import Base
from extras.app.database.session import get_db
from extras.app.main import app

# Use isolated SQLite database for testing
TEST_DATABASE_URL = "sqlite:///./test_extras.db"

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_extras.db"):
        try:
            os.remove("./test_extras.db")
        except Exception:
            pass

@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_messages():
    path = "sample_data/extras/messages.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def sample_voices():
    path = "sample_data/extras/voice_transcripts.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

