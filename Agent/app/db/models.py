# @XobierWang

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(128))
    gender: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    id_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    course_records: Mapped[list["CourseRecord"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    learning_sessions: Mapped[list["LearningSession"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    memory_preference: Mapped[Optional["MemoryPreference"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    user_profile: Mapped[Optional["UserProfile"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    memory_events: Mapped[list["MemoryEvent"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    conversation_memories: Mapped[list["ConversationMemory"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )


class CourseRecord(Base):
    __tablename__ = "course_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    course_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    assessment: Mapped[str] = mapped_column(String(255))
    objective: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    performance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    background: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    study_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    teacher: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped["Student"] = relationship(back_populates="course_records")


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    session_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    session_type: Mapped[str] = mapped_column(String(32))
    department: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    teacher_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    session_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped["Student"] = relationship(back_populates="learning_sessions")


class MemoryPreference(Base):
    __tablename__ = "memory_preferences"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"), unique=True, index=True
    )
    preferred_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    response_style: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    response_length: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    preferred_language: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    focus_topics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    additional_preferences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped["Student"] = relationship(back_populates="memory_preference")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"), unique=True, index=True
    )
    profile_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    communication_style: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    preferred_topics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stable_preferences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped["Student"] = relationship(back_populates="user_profile")


class MemoryEvent(Base):
    __tablename__ = "memory_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    event_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(64))
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped["Student"] = relationship(back_populates="memory_events")


class ConversationMemory(Base):
    __tablename__ = "conversation_memories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    session_id: Mapped[str] = mapped_column(String(128), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    multimodal_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    student: Mapped["Student"] = relationship(back_populates="conversation_memories")
