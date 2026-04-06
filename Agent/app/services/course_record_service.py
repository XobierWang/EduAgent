# @XobierWang

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CourseRecord, Student
from app.schemas.course_record import CourseRecordCreate, CourseRecordUpdate


def create_course_record(db: Session, payload: CourseRecordCreate) -> CourseRecord:
    course_record = CourseRecord(**payload.model_dump(exclude_none=True))
    db.add(course_record)
    db.commit()
    db.refresh(course_record)
    return course_record


def get_course_record_by_id(db: Session, case_id: int) -> Optional[CourseRecord]:
    return db.get(CourseRecord, case_id)


def list_course_records(
    db: Session, student_id: Optional[int] = None
) -> list[CourseRecord]:
    stmt = select(CourseRecord).order_by(CourseRecord.recorded_at.desc())
    if student_id is not None:
        stmt = stmt.where(CourseRecord.student_id == student_id)
    return list(db.scalars(stmt).all())


def update_course_record(
    db: Session, course_record: CourseRecord, payload: CourseRecordUpdate
) -> CourseRecord:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(course_record, field, value)
    db.add(course_record)
    db.commit()
    db.refresh(course_record)
    return course_record


def student_exists(db: Session, student_id: int) -> bool:
    return db.get(Student, student_id) is not None
