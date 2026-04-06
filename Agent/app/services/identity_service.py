# @XobierWang

from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import Student
from app.services import student_service


def mask_id_number(id_number: Optional[str]) -> Optional[str]:
    if not id_number or len(id_number) < 8:
        return id_number
    return f"{id_number[:4]}********{id_number[-4:]}"


def mask_phone(phone: Optional[str]) -> Optional[str]:
    if not phone or len(phone) < 7:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"


def verify_student_identity(
    db: Session,
    student_code: str,
    phone: Optional[str] = None,
    id_number: Optional[str] = None,
) -> dict:
    student = student_service.get_student_by_code(db, student_code)
    if student is None:
        return {
            "verified": False,
            "reason": "student not found",
            "student_code": student_code,
        }

    if not phone and not id_number:
        return {
            "verified": False,
            "reason": "phone or id_number is required",
            "student_code": student_code,
        }

    phone_match = phone is not None and phone == student.phone
    id_match = id_number is not None and id_number == student.id_number

    verified = phone_match or id_match
    return {
        "verified": verified,
        "reason": "ok" if verified else "credential mismatch",
        "student": serialize_student_identity(student),
    }


def serialize_student_identity(student: Student) -> dict:
    return {
        "id": student.id,
        "student_code": student.student_code,
        "full_name": student.full_name,
        "gender": student.gender,
        "phone_masked": mask_phone(student.phone),
        "id_number_masked": mask_id_number(student.id_number),
    }
