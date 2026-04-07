# @XobierWang

from __future__ import annotations

from datetime import datetime
import logging
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import (
    ConversationMemory,
    CourseRecord,
    MemoryEvent,
    MemoryPreference,
    Student,
    UserProfile,
    LearningSession,
)
from app.services import (
    course_record_service,
    memory_vector_service,
    student_service,
    learning_session_service,
)

logger = logging.getLogger("uvicorn.error")


MEDICAL_KEYWORDS = [
    "数学",
    "冠心病",
    "心绞痛",
    "高血压",
    "糖尿病",
    "辅导",
    "用药",
    "检查",
    "住院",
]

STYLE_KEYWORDS = {
    "简短": "简洁",
    "简单": "简洁",
    "直接": "直接给结论",
    "详细": "详细说明",
    "通俗": "通俗解释",
    "专业": "专业表达",
}


EVENT_MATCH_KEYWORDS = [
    "最近",
    "最新",
    "辅导",
    "住院",
    "用药",
    "检查",
    "数学",
    "胸痛",
    "心绞痛",
    "冠心病",
    "教师",
]


def get_student(db: Session, student_id: Optional[int], student_code: Optional[str]) -> Optional[Student]:
    if student_id is not None:
        return student_service.get_student_by_id(db, student_id)
    if student_code is not None:
        return student_service.get_student_by_code(db, student_code)
    return None


def list_memory_events(db: Session, student_id: int) -> list[MemoryEvent]:
    stmt = (
        select(MemoryEvent)
        .where(MemoryEvent.student_id == student_id)
        .order_by(MemoryEvent.event_time.desc(), MemoryEvent.id.desc())
    )
    return list(db.scalars(stmt).all())


def get_user_profile(db: Session, student_id: int) -> Optional[UserProfile]:
    stmt = select(UserProfile).where(UserProfile.student_id == student_id)
    return db.scalar(stmt)


def get_relevant_memory_events(
    db: Session,
    student_id: int,
    query: str,
    limit: int = 5,
) -> list[MemoryEvent]:
    results = search_memory_events(db, student_id, query, top_n=limit)
    return [item["event"] for item in results]


def get_conversation_texts_for_extraction(
    db: Session,
    student_id: int,
    session_id: Optional[str] = None,
    limit: int = 10,
) -> list[str]:
    stmt = (
        select(ConversationMemory)
        .where(ConversationMemory.student_id == student_id)
        .order_by(ConversationMemory.created_at.desc(), ConversationMemory.id.desc())
        .limit(limit)
    )
    if session_id is not None:
        stmt = stmt.where(ConversationMemory.session_id == session_id)
    memories = list(db.scalars(stmt).all())
    memories.reverse()
    return [memory.content for memory in memories if memory.content.strip()]


def refresh_business_memory(
    db: Session,
    student: Student,
) -> list[MemoryEvent]:
    events = _rebuild_business_memory_events(db, student)
    db.commit()
    logger.info(
        "Business memory extracted for student_id=%s student_code=%s event_count=%s",
        student.id,
        student.student_code,
        len(events),
    )
    memory_vector_service.replace_memory_events(
        student_id=student.id,
        events=events,
        source_types=["course_record", "learning_session"],
    )
    return events


def refresh_conversation_memory(
    db: Session,
    student: Student,
    conversation_texts: list[str],
) -> tuple[list[MemoryEvent], UserProfile]:
    events = _rebuild_conversation_memory_events(db, student, conversation_texts)
    profile = _upsert_user_profile(db, student, conversation_texts)
    db.commit()
    logger.info(
        "Conversation memory extracted for student_id=%s student_code=%s event_count=%s conversation_count=%s",
        student.id,
        student.student_code,
        len(events),
        len(conversation_texts),
    )
    memory_vector_service.replace_memory_events(
        student_id=student.id,
        events=events,
        source_types=["conversation"],
    )
    db.refresh(profile)
    return events, profile


def search_memory_events(
    db: Session,
    student_id: int,
    query: str,
    top_n: int = 5,
) -> list[dict]:
    events = list_memory_events(db, student_id)
    if not events:
        logger.info("No memory events available for hybrid search student_id=%s", student_id)
        return []

    event_map = {event.id: event for event in events}
    ranked: dict[int, dict] = {}
    query_keywords = [keyword for keyword in EVENT_MATCH_KEYWORDS if keyword in query]

    for event in events:
        keyword_hits = _count_keyword_hits(query_keywords, event)
        if keyword_hits <= 0:
            continue
        keyword_score = 0.6 + min(keyword_hits, 5) * 0.08
        ranked[event.id] = {
            "event": event,
            "retrieval_score": keyword_score,
            "retrieval_sources": ["keyword"],
            "keyword_score": keyword_score,
            "vector_score": 0.0,
        }

    vector_rows = memory_vector_service.search_memory_events(
        student_id=student_id,
        query=query,
        top_n=top_n * 2,
    )
    for row in vector_rows:
        event = event_map.get(row["event_id"])
        if event is None:
            continue
        vector_score = row["vector_score"] * 0.7
        existing = ranked.get(event.id)
        if existing is None:
            ranked[event.id] = {
                "event": event,
                "retrieval_score": vector_score,
                "retrieval_sources": ["vector"],
                "keyword_score": 0.0,
                "vector_score": vector_score,
            }
            continue
        existing["retrieval_score"] += vector_score
        existing["vector_score"] += vector_score
        if "vector" not in existing["retrieval_sources"]:
            existing["retrieval_sources"].append("vector")

    results = sorted(
        ranked.values(),
        key=lambda item: (
            item["retrieval_score"],
            item["event"].event_time,
            item["event"].id,
        ),
        reverse=True,
    )
    if results:
        logger.info(
            "Hybrid memory search student_id=%s query=%r top_n=%s keyword_hits=%s vector_hits=%s merged_hits=%s",
            student_id,
            query,
            top_n,
            sum(1 for item in ranked.values() if "keyword" in item["retrieval_sources"]),
            len(vector_rows),
            len(results[:top_n]),
        )
        return results[:top_n]

    logger.info(
        "Hybrid memory search fallback to recent events for student_id=%s query=%r top_n=%s",
        student_id,
        query,
        top_n,
    )
    return [
        {
            "event": event,
            "retrieval_score": 0.0,
            "retrieval_sources": ["recent"],
            "keyword_score": 0.0,
            "vector_score": 0.0,
        }
        for event in events[:top_n]
    ]


def _rebuild_business_memory_events(
    db: Session,
    student: Student,
) -> list[MemoryEvent]:
    db.execute(
        delete(MemoryEvent).where(
            MemoryEvent.student_id == student.id,
            MemoryEvent.source_type.in_(["course_record", "learning_session"]),
        )
    )

    events: list[MemoryEvent] = []
    course_records = course_record_service.list_course_records(db, student_id=student.id)
    learning_sessions = learning_session_service.list_learning_sessions(db, student_id=student.id)

    for course_record in course_records:
        events.append(
            MemoryEvent(
                student_id=student.id,
                event_type="course_record",
                event_time=course_record.recorded_at,
                title=f"课程记录评估：{course_record.diagnosis}",
                summary=course_record.chief_complaint or course_record.treatment_plan,
                source_type="course_record",
                source_id=str(course_record.id),
            )
        )

    for learning_session in learning_sessions:
        events.append(
            MemoryEvent(
                student_id=student.id,
                event_type="learning_session",
                event_time=learning_session.visit_time,
                title=f"{learning_session.department or '课程'}学习",
                summary=learning_session.summary or learning_session.notes,
                source_type="learning_session",
                source_id=str(learning_session.id),
            )
        )

    for event in events:
        db.add(event)
    db.flush()
    return [
        event
        for event in list_memory_events(db, student.id)
        if event.source_type in {"course_record", "learning_session"}
    ]


def _rebuild_conversation_memory_events(
    db: Session,
    student: Student,
    conversation_texts: list[str],
) -> list[MemoryEvent]:
    db.execute(
        delete(MemoryEvent).where(
            MemoryEvent.student_id == student.id,
            MemoryEvent.source_type == "conversation",
        )
    )

    events: list[MemoryEvent] = []
    for index, text in enumerate(conversation_texts, start=1):
        if not text.strip():
            continue
        matched_keywords = [keyword for keyword in MEDICAL_KEYWORDS if keyword in text]
        if not matched_keywords:
            continue
        events.append(
            MemoryEvent(
                student_id=student.id,
                event_type="conversation_medical_hint",
                event_time=datetime.utcnow(),
                title=f"对话提及：{'、'.join(matched_keywords[:3])}",
                summary=text[:300],
                source_type="conversation",
                source_id=f"conversation-{index}",
            )
        )

    for event in events:
        db.add(event)
    db.flush()
    return [event for event in list_memory_events(db, student.id) if event.source_type == "conversation"]


def _upsert_user_profile(
    db: Session,
    student: Student,
    conversation_texts: list[str],
) -> UserProfile:
    profile = get_user_profile(db, student.id)
    if profile is None:
        profile = UserProfile(student_id=student.id)

    preference = _get_memory_preference(db, student.id)
    conversation_blob = "\n".join(conversation_texts)
    topics = _extract_topics(student, preference, conversation_blob)
    communication_style = _extract_communication_style(preference, conversation_blob)
    stable_preferences = _build_stable_preferences(preference, communication_style)
    profile.profile_summary = _build_profile_summary(student, topics, stable_preferences)
    profile.communication_style = communication_style
    profile.preferred_topics = topics
    profile.stable_preferences = stable_preferences
    profile.source_summary = _build_source_summary(preference, conversation_texts)
    profile.refreshed_at = datetime.utcnow()

    db.add(profile)
    db.flush()
    return profile


def _get_memory_preference(db: Session, student_id: int) -> Optional[MemoryPreference]:
    stmt = select(MemoryPreference).where(MemoryPreference.student_id == student_id)
    return db.scalar(stmt)


def _extract_topics(
    student: Student,
    preference: Optional[MemoryPreference],
    conversation_blob: str,
) -> str:
    topics: list[str] = []
    if preference and preference.focus_topics:
        topics.extend(_split_items(preference.focus_topics))
    for keyword in MEDICAL_KEYWORDS:
        if keyword in conversation_blob and keyword not in topics:
            topics.append(keyword)
    return "、".join(topics[:6]) or "常规健康咨询"


def _extract_communication_style(
    preference: Optional[MemoryPreference],
    conversation_blob: str,
) -> str:
    if preference and preference.response_style:
        return preference.response_style
    styles = [value for keyword, value in STYLE_KEYWORDS.items() if keyword in conversation_blob]
    return "、".join(dict.fromkeys(styles)) if styles else "稳健、清晰"


def _build_stable_preferences(
    preference: Optional[MemoryPreference],
    communication_style: str,
) -> str:
    parts: list[str] = []
    if preference and preference.preferred_name:
        parts.append(f"偏好称呼：{preference.preferred_name}")
    if preference and preference.response_length:
        parts.append(f"回答长度：{preference.response_length}")
    if preference and preference.preferred_language:
        parts.append(f"语言：{preference.preferred_language}")
    parts.append(f"表达风格：{communication_style}")
    if preference and preference.additional_preferences:
        parts.append(f"补充偏好：{preference.additional_preferences}")
    return "；".join(parts)


def _build_profile_summary(
    student: Student,
    topics: str,
    stable_preferences: str,
) -> str:
    return (
        f"{student.full_name}（{student.student_code}）长期关注{topics}相关内容。"
        f"稳定偏好：{stable_preferences}。"
    )


def _build_source_summary(
    preference: Optional[MemoryPreference],
    conversation_texts: list[str],
) -> str:
    source_parts = ["业务数据：课程记录与诊疗记录"]
    if preference is not None:
        source_parts.append("用户配置：长期偏好设置")
    if conversation_texts:
        source_parts.append(f"短期对话：{len(conversation_texts)}段")
    return "；".join(source_parts)


def _split_items(text: str) -> list[str]:
    normalized = text.replace("，", ",").replace("、", ",").replace("；", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def _count_keyword_hits(query_keywords: list[str], event: MemoryEvent) -> int:
    if not query_keywords:
        return 0
    haystack = f"{event.title} {event.summary or ''}"
    return sum(1 for keyword in query_keywords if keyword in haystack)
