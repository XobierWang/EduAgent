# @XobierWang

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Student
from app.schemas.student import StudentCreate, StudentUpdate


def create_student(db: Session, payload: StudentCreate) -> Student:
    student = Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def list_students(db: Session) -> list[Student]:
    return list(db.scalars(select(Student).order_by(Student.id.desc())).all())


def get_student_by_id(db: Session, student_id: int) -> Optional[Student]:
    return db.get(Student, student_id)


def get_student_by_code(db: Session, student_code: str) -> Optional[Student]:
    stmt = select(Student).where(Student.student_code == student_code)
    return db.scalar(stmt)


def get_student_by_phone(db: Session, phone: str) -> Optional[Student]:
    stmt = select(Student).where(Student.phone == phone)
    return db.scalar(stmt)


def update_student(db: Session, student: Student, payload: StudentUpdate) -> Student:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student
