# @XobierWang

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CourseRecordBase(BaseModel):
    student_id: int
    course_code: str
    assessment: str
    objective: Optional[str] = None
    performance: Optional[str] = None
    background: Optional[str] = None
    study_plan: Optional[str] = None
    teacher: Optional[str] = None
    recorded_at: Optional[datetime] = None


class CourseRecordCreate(CourseRecordBase):
    pass


class CourseRecordUpdate(BaseModel):
    assessment: Optional[str] = None
    objective: Optional[str] = None
    performance: Optional[str] = None
    background: Optional[str] = None
    study_plan: Optional[str] = None
    teacher: Optional[str] = None
    recorded_at: Optional[datetime] = None


class CourseRecordRead(CourseRecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime
