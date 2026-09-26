import os
os.environ["DATABASE_URL"] = "sqlite:///./test_fitbuddy.db"
os.environ["GEMINI_API_KEY"] = "test-key"
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield

@pytest.fixture
def client():
    return TestClient(app)
