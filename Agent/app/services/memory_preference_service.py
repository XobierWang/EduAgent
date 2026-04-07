# @XobierWang

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MemoryPreference, Student
from app.schemas.memory_preference import MemoryPreferenceUpsert


def get_memory_preference_by_student_id(
    db: Session, student_id: int
) -> Optional[MemoryPreference]:
    stmt = select(MemoryPreference).where(MemoryPreference.student_id == student_id)
    return db.scalar(stmt)


def get_memory_preference_by_student_code(
    db: Session, student_code: str
) -> Optional[MemoryPreference]:
    stmt = (
        select(MemoryPreference)
        .join(Student, Student.id == MemoryPreference.student_id)
        .where(Student.student_code == student_code)
    )
    return db.scalar(stmt)


def upsert_memory_preference(
    db: Session, payload: MemoryPreferenceUpsert
) -> MemoryPreference:
    memory_preference = get_memory_preference_by_student_id(db, payload.student_id)
    if memory_preference is None:
        memory_preference = MemoryPreference(student_id=payload.student_id)

    for field, value in payload.model_dump().items():
        if field == "student_id":
            continue
        setattr(memory_preference, field, value)

    db.add(memory_preference)
    db.commit()
    db.refresh(memory_preference)
    return memory_preference
