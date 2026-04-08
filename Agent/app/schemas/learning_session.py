# @XobierWang

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LearningSessionBase(BaseModel):
    student_id: int
    session_code: str
    session_type: str
    department: Optional[str] = None
    teacher_name: Optional[str] = None
    session_time: Optional[datetime] = None
    summary: Optional[str] = None
    notes: Optional[str] = None


class LearningSessionCreate(LearningSessionBase):
    pass


class LearningSessionUpdate(BaseModel):
    session_type: Optional[str] = None
    department: Optional[str] = None
    teacher_name: Optional[str] = None
    session_time: Optional[datetime] = None
    summary: Optional[str] = None
    notes: Optional[str] = None


class LearningSessionRead(LearningSessionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_time: datetime
    created_at: datetime
    updated_at: datetime
