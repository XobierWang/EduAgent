# @XobierWang

from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import CourseRecord, Student, LearningSession
from app.services import identity_service, course_record_service, student_service, learning_session_service


def serialize_student(student: Student) -> dict:
    return {
        "id": student.id,
        "student_code": student.student_code,
        "full_name": student.full_name,
        "gender": student.gender,
        "date_of_birth": student.date_of_birth.isoformat()
        if student.date_of_birth
        else None,
        "phone": student.phone,
        "id_number": student.id_number,
        "address": student.address,
        "emergency_contact_name": student.emergency_contact_name,
        "emergency_contact_phone": student.emergency_contact_phone,
        "created_at": student.created_at.isoformat(),
        "updated_at": student.updated_at.isoformat(),
    }


def serialize_course_record(course_record: CourseRecord) -> dict:
    return {
        "id": course_record.id,
        "student_id": course_record.student_id,
        "course_code": course_record.course_code,
        "assessment": course_record.assessment,
        "objective": course_record.objective,
        "performance": course_record.performance,
        "background": course_record.background,
        "study_plan": course_record.study_plan,
        "teacher": course_record.teacher,
        "recorded_at": course_record.recorded_at.isoformat(),
        "created_at": course_record.created_at.isoformat(),
        "updated_at": course_record.updated_at.isoformat(),
    }


def serialize_learning_session(learning_session: LearningSession) -> dict:
    return {
        "id": learning_session.id,
        "student_id": learning_session.student_id,
        "session_code": learning_session.session_code,
        "session_type": learning_session.session_type,
        "department": learning_session.department,
        "teacher_name": learning_session.teacher_name,
        "session_time": learning_session.session_time.isoformat(),
        "summary": learning_session.summary,
        "notes": learning_session.notes,
        "created_at": learning_session.created_at.isoformat(),
        "updated_at": learning_session.updated_at.isoformat(),
    }


def get_student_profile(
    db: Session,
    student_id: Optional[int] = None,
    student_code: Optional[str] = None,
) -> dict:
    student = None
    if student_id is not None:
        student = student_service.get_student_by_id(db, student_id)
    elif student_code is not None:
        student = student_service.get_student_by_code(db, student_code)

    if student is None:
        return {"found": False, "reason": "student not found"}

    return {"found": True, "student": serialize_student(student)}


def get_student_course_records(
    db: Session,
    student_id: Optional[int] = None,
    student_code: Optional[str] = None,
) -> dict:
    student = _resolve_student(db, student_id=student_id, student_code=student_code)
    if student is None:
        return {"found": False, "reason": "student not found", "course_records": []}

    course_records = course_record_service.list_course_records(db, student_id=student.id)
    return {
        "found": True,
        "student": identity_service.serialize_student_identity(student),
        "course_records": [serialize_course_record(item) for item in course_records],
    }


def get_student_learning_sessions(
    db: Session,
    student_id: Optional[int] = None,
    student_code: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    student = _resolve_student(db, student_id=student_id, student_code=student_code)
    if student is None:
        return {"found": False, "reason": "student not found", "learning_sessions": []}

    learning_sessions = learning_session_service.list_learning_sessions(
        db,
        student_id=student.id,
        limit=limit,
    )
    return {
        "found": True,
        "student": identity_service.serialize_student_identity(student),
        "count": len(learning_sessions),
        "learning_sessions": [serialize_learning_session(item) for item in learning_sessions],
    }


def verify_student(
    db: Session,
    student_code: str,
    phone: Optional[str] = None,
    id_number: Optional[str] = None,
) -> dict:
    return identity_service.verify_student_identity(
        db,
        student_code=student_code,
        phone=phone,
        id_number=id_number,
    )


def _resolve_student(
    db: Session,
    student_id: Optional[int] = None,
    student_code: Optional[str] = None,
) -> Optional[Student]:
    if student_id is not None:
        return student_service.get_student_by_id(db, student_id)
    if student_code is not None:
        return student_service.get_student_by_code(db, student_code)
    return None
