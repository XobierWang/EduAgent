# @XobierWang

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Student, LearningSession
from app.schemas.learning_session import LearningSessionCreate, LearningSessionUpdate


def create_learning_session(db: Session, payload: LearningSessionCreate) -> LearningSession:
    learning_session = LearningSession(**payload.model_dump(exclude_none=True))
    db.add(learning_session)
    db.commit()
    db.refresh(learning_session)
    return learning_session


def get_learning_session_by_id(
    db: Session, learning_session_id: int
) -> Optional[LearningSession]:
    return db.get(LearningSession, learning_session_id)


def list_learning_sessions(
    db: Session,
    student_id: Optional[int] = None,
    limit: Optional[int] = None,
) -> list[LearningSession]:
    stmt = select(LearningSession).order_by(LearningSession.visit_time.desc())
    if student_id is not None:
        stmt = stmt.where(LearningSession.student_id == student_id)
    if limit is not None and limit > 0:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt).all())


def update_learning_session(
    db: Session, learning_session: LearningSession, payload: LearningSessionUpdate
) -> LearningSession:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(learning_session, field, value)
    db.add(learning_session)
    db.commit()
    db.refresh(learning_session)
    return learning_session


def student_exists(db: Session, student_id: int) -> bool:
    return db.get(Student, student_id) is not None
