# @XobierWang

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CourseRecordBase(BaseModel):
    student_id: int
    case_code: str
    diagnosis: str
    chief_complaint: Optional[str] = None
    present_illness: Optional[str] = None
    past_history: Optional[str] = None
    treatment_plan: Optional[str] = None
    attending_physician: Optional[str] = None
    recorded_at: Optional[datetime] = None


class CourseRecordCreate(CourseRecordBase):
    pass


class CourseRecordUpdate(BaseModel):
    diagnosis: Optional[str] = None
    chief_complaint: Optional[str] = None
    present_illness: Optional[str] = None
    past_history: Optional[str] = None
    treatment_plan: Optional[str] = None
    attending_physician: Optional[str] = None
    recorded_at: Optional[datetime] = None


class CourseRecordRead(CourseRecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime
