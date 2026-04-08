import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.init_db import _ensure_sqlite_columns
from app.main import app


@pytest.fixture(scope="session")
def engine():
    tmpdir = tempfile.mkdtemp()
    db_path = Path(tmpdir) / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db(engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    from app.db.session import get_db

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield session

    app.dependency_overrides.clear()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db) -> TestClient:
    return TestClient(app)


@pytest.fixture
def sample_student(client):
    resp = client.post("/api/students", json={
        "student_code": "S2024001",
        "full_name": "Zhang San",
        "gender": "male",
        "phone": "13800001111",
        "id_number": "310101200501011234",
    })
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def sample_course_record(client, sample_student):
    resp = client.post("/api/course-records", json={
        "student_id": sample_student["id"],
        "course_code": "C2024001",
        "assessment": "Good progress in calculus",
        "objective": "Master differentiation techniques",
        "performance": "Completed 8/10 exercises correctly",
        "background": "Prior exposure to basic algebra",
        "study_plan": "Focus on integration next week",
        "teacher": "Prof. Wang",
    })
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def sample_learning_session(client, sample_student):
    resp = client.post("/api/learning-sessions", json={
        "student_id": sample_student["id"],
        "session_code": "LS2024001",
        "session_type": "tutorial",
        "teacher_name": "Prof. Li",
        "department": "Mathematics",
        "session_time": "2024-03-15T14:00:00",
        "summary": "Reviewed differential equations",
        "notes": "Student shows strong analytical skills",
    })
    assert resp.status_code == 201
    return resp.json()
