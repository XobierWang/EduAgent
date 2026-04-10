# @XobierWang

import base64
import json
import logging
import re
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from openai import BadRequestError
from sqlalchemy.orm import Session

from app.db.session import DATA_DIR
from app.db.session import get_db
from app.llm.qwen_client import QwenClient
from app.llm.qwen_mcp_agent import QwenMCPAgent
from app.llm.qwen_speech_client import QwenSpeechClient
from app.schemas.agent import AgentQueryRequest, AgentQueryResponse
from app.schemas.memory import (
    BusinessMemoryExtractRequest,
    BusinessMemoryExtractResponse,
    ConversationMemoryCreate,
    ConversationMemoryRead,
    ConversationMemoryExtractRequest,
    ConversationMemoryExtractResponse,
    MemoryEventRead,
    MemoryEventSearchRequest,
    MemoryEventSearchResponse,
    MemoryEventSearchItem,
    UserProfileRead,
)
from app.schemas.memory_preference import MemoryPreferenceRead, MemoryPreferenceUpsert
from app.schemas.course_record import CourseRecordCreate, CourseRecordRead, CourseRecordUpdate
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate
from app.schemas.learning_session import (
    LearningSessionCreate,
    LearningSessionRead,
    LearningSessionUpdate,
)
from app.services import (
    memory_preference_service,
    memory_service,
    course_record_service,
    student_service,
    learning_session_service,
    conversation_memory_service,
)

router = APIRouter()
logger = logging.getLogger("uvicorn.error")
GENERATED_AUDIO_DIR = DATA_DIR / "generated_audio"
GENERATED_AUDIO_DIR.mkdir(exist_ok=True)
SHORT_TERM_ROUND_TRIGGER = 5
MESSAGES_PER_ROUND = 2
SHORT_TERM_TRIGGER_MESSAGE_COUNT = SHORT_TERM_ROUND_TRIGGER * MESSAGES_PER_ROUND


def _save_speech_audio(audio_base64: str, mime_type: str) -> tuple[str, str]:
    suffix = ".mp3" if mime_type == "audio/mp3" else ".bin"
    filename = f"speech_{uuid4().hex}{suffix}"
    output_path = GENERATED_AUDIO_DIR / filename
    output_path.write_bytes(base64.b64decode(audio_base64))
    return str(output_path), f"/media/generated_audio/{filename}"


def _extract_student_code_from_query(query: str) -> Optional[str]:
    match = re.search(r"P\d{4,}", query, flags=re.IGNORECASE)
    if match is None:
        return None
    return match.group(0).upper()


def _extract_phone_from_query(query: str) -> Optional[str]:
    match = re.search(r"1\d{10}", query)
    if match is None:
        return None
    return match.group(0)


def _build_user_multimodal_payload(payload: AgentQueryRequest) -> Optional[str]:
    if not payload.images:
        return None
    image_items = []
    for image in payload.images:
        image_items.append(
            {
                "mime_type": image.mime_type,
                "image_url": image.image_url,
                "has_base64": bool(image.image_base64),
            }
        )
    return json.dumps({"images": image_items}, ensure_ascii=False)


def _build_assistant_multimodal_payload(result: dict) -> Optional[str]:
    if not result.get("speech_download_url") and not result.get("speech_file_path"):
        return None
    return json.dumps(
        {
            "speech": {
                "speech_mime_type": result.get("speech_mime_type"),
                "speech_model": result.get("speech_model"),
                "speech_voice": result.get("speech_voice"),
                "speech_file_path": result.get("speech_file_path"),
                "speech_download_url": result.get("speech_download_url"),
            }
        },
        ensure_ascii=False,
    )


def _build_retrieval_label(retrieval_sources: list[str]) -> str:
    sources = set(retrieval_sources)
    if {"keyword", "vector"}.issubset(sources):
        return "hybrid"
    if "keyword" in sources:
        return "keyword"
    if "vector" in sources:
        return "vector"
    return "recent"


def _resolve_student_from_agent_result(
    db: Session,
    query: str,
    result: dict,
):
    for tool_output in result.get("tool_outputs", []):
        tool_name = tool_output.get("tool_name")
        tool_result = tool_output.get("result", {})

        if tool_name == "verify_student_identity" and tool_result.get("verified"):
            student_data = tool_result.get("student", {})
            student_id = student_data.get("id")
            if student_id is not None:
                student = student_service.get_student_by_id(db, student_id)
                if student is not None:
                    return student
            student_code = student_data.get("student_code")
            if student_code:
                student = student_service.get_student_by_code(db, student_code)
                if student is not None:
                    return student

        student_data = tool_result.get("student")
        if isinstance(student_data, dict):
            student_id = student_data.get("id")
            if student_id is not None:
                student = student_service.get_student_by_id(db, student_id)
                if student is not None:
                    return student
            student_code = student_data.get("student_code")
            if student_code:
                student = student_service.get_student_by_code(db, student_code)
                if student is not None:
                    return student

    student_code = _extract_student_code_from_query(query)
    if student_code is not None:
        student = student_service.get_student_by_code(db, student_code)
        if student is not None:
            return student

    phone = _extract_phone_from_query(query)
    if phone is not None:
        return student_service.get_student_by_phone(db, phone)
    return None


def _build_memory_context(db: Session, student, query: str) -> dict:
    short_term_memories = conversation_memory_service.list_recent_conversation_memories(
        db,
        student_id=student.id,
        limit=6,
    )
    user_profile = memory_service.get_user_profile(db, student.id)
    relevant_events = memory_service.get_relevant_memory_events(
        db,
        student_id=student.id,
        query=query,
        limit=5,
    )
    return {
        "short_term_memories": [
            {
                "role": memory.role,
                "content": memory.content,
                "multimodal_payload": memory.multimodal_payload,
            }
            for memory in short_term_memories
        ],
        "user_profile": (
            {
                "profile_summary": user_profile.profile_summary,
                "stable_preferences": user_profile.stable_preferences,
                "preferred_topics": user_profile.preferred_topics,
            }
            if user_profile is not None
            else None
        ),
        "relevant_events": [
            {
                "event_time": event.event_time.isoformat(),
                "title": event.title,
                "summary": event.summary,
            }
            for event in relevant_events
        ],
    }


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/agent/query",
    response_model=AgentQueryResponse,
    tags=["Agent"],
    summary="调用 Qwen + 工具查询学生信息",
    description=(
        "主问答接口。把用户的问题发送给 Agent，由 Agent 结合历史短期记忆、长期用户画像、"
        "长期关键事件、内部工具和可选图片一起生成答案。"
        "如果开启语音播报，还会额外生成音频文件路径和下载链接。"
    ),
)
def agent_query(
    request: Request,
    payload: AgentQueryRequest,
    db: Session = Depends(get_db),
) -> AgentQueryResponse:
    try:
        llm_client = QwenClient()
        speech_client = QwenSpeechClient() if payload.enable_speech else None
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    agent = QwenMCPAgent(db=db, llm_client=llm_client)
    try:
        pre_resolved_student = _resolve_student_from_agent_result(
            db,
            payload.query,
            {"tool_outputs": []},
        )
        memory_context = None
        if pre_resolved_student is not None:
            memory_context = _build_memory_context(db, pre_resolved_student, payload.query)
        result = agent.run(
            payload.query,
            images=[image.model_dump() for image in payload.images],
            debug_planner=payload.debug_planner,
            memory_context=memory_context,
        )
    except BadRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    if payload.enable_speech and speech_client is not None:
        try:
            speech_result = speech_client.synthesize(
                result["answer"],
                voice=payload.speech_voice,
                audio_format=payload.speech_format,
            )
        except (BadRequestError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )
        speech_file_path, speech_download_url = _save_speech_audio(
            speech_result["audio_base64"],
            speech_result["mime_type"],
        )
        result.update(
            {
                "speech_mime_type": speech_result["mime_type"],
                "speech_model": speech_result["model"],
                "speech_voice": speech_result["voice"],
                "speech_file_path": speech_file_path,
                "speech_download_url": str(request.base_url).rstrip("/") + speech_download_url,
            }
        )

    student = _resolve_student_from_agent_result(db, payload.query, result)
    if student is not None:
        memory_session_id = f"agent-{uuid4().hex}"
        conversation_memory_service.create_conversation_memory(
            db,
            ConversationMemoryCreate(
                student_id=student.id,
                session_id=memory_session_id,
                role="user",
                content=payload.query,
                multimodal_payload=_build_user_multimodal_payload(payload),
            ),
        )
        conversation_memory_service.create_conversation_memory(
            db,
            ConversationMemoryCreate(
                student_id=student.id,
                session_id=memory_session_id,
                role="assistant",
                content=result["answer"],
                multimodal_payload=_build_assistant_multimodal_payload(result),
            ),
        )
        short_term_count = conversation_memory_service.count_conversation_memories(
            db,
            student_id=student.id,
        )
        if (
            short_term_count >= SHORT_TERM_TRIGGER_MESSAGE_COUNT
            and short_term_count % SHORT_TERM_TRIGGER_MESSAGE_COUNT == 0
        ):
            conversation_texts = memory_service.get_conversation_texts_for_extraction(
                db=db,
                student_id=student.id,
                limit=SHORT_TERM_TRIGGER_MESSAGE_COUNT,
            )
            memory_events, user_profile = memory_service.refresh_conversation_memory(
                db=db,
                student=student,
                conversation_texts=conversation_texts,
            )
            logger.info(
                "Auto extracted long-term conversation memory for student_id=%s short_term_count=%s event_count=%s profile_updated=%s",
                student.id,
                short_term_count,
                len(memory_events),
                user_profile is not None,
            )
    return AgentQueryResponse(**result)


@router.get(
    "/memory/preferences",
    response_model=MemoryPreferenceRead,
    tags=["Memory"],
    summary="查询长期记忆偏好配置",
    description=(
        "读取某个学生已经保存的长期偏好配置，例如偏好称呼、回答风格、回答长度、"
        "常关注主题等。这些内容会影响后续 Agent 的个性化回答。"
    ),
)
def get_memory_preference(
    student_id: Optional[int] = Query(default=None),
    student_code: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> MemoryPreferenceRead:
    if student_id is None and student_code is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="student_id or student_code is required",
        )

    memory_preference = None
    if student_id is not None:
        memory_preference = memory_preference_service.get_memory_preference_by_student_id(
            db, student_id
        )
    elif student_code is not None:
        memory_preference = memory_preference_service.get_memory_preference_by_student_code(
            db, student_code
        )

    if memory_preference is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="memory preference not found",
        )
    return memory_preference


@router.put(
    "/memory/preferences",
    response_model=MemoryPreferenceRead,
    tags=["Memory"],
    summary="创建或更新长期记忆偏好配置",
    description=(
        "创建或更新某个学生的长期偏好。这个接口适合保存用户主动设置的内容，"
        "例如希望回答更简短、希望使用通俗语言、关注数学等。"
    ),
)
def upsert_memory_preference(
    payload: MemoryPreferenceUpsert,
    db: Session = Depends(get_db),
) -> MemoryPreferenceRead:
    student = student_service.get_student_by_id(db, payload.student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="student not found",
        )
    return memory_preference_service.upsert_memory_preference(db, payload)


@router.post(
    "/memory/conversations",
    response_model=ConversationMemoryRead,
    tags=["Memory"],
    summary="写入短期记忆对话",
    description=(
        "手动写入一条短期记忆。通常系统会在 /api/agent/query 完成后自动写入，"
        "这个接口更适合测试、补数据或联调。"
    ),
)
def create_conversation_memory(
    payload: ConversationMemoryCreate,
    db: Session = Depends(get_db),
) -> ConversationMemoryRead:
    student = student_service.get_student_by_id(db, payload.student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="student not found",
        )
    return conversation_memory_service.create_conversation_memory(db, payload)


@router.get(
    "/memory/conversations",
    response_model=list[ConversationMemoryRead],
    tags=["Memory"],
    summary="查询短期记忆对话",
    description=(
        "查询某个学生已经保存的短期记忆内容。可以按 session_id 过滤，也可以限制返回条数，"
        "适合查看最近几轮对话是否已经正确写入。"
    ),
)
def list_conversation_memories(
    student_id: int,
    session_id: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=10),
    db: Session = Depends(get_db),
) -> list[ConversationMemoryRead]:
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="student not found",
        )
    return conversation_memory_service.list_conversation_memories(
        db,
        student_id=student_id,
        session_id=session_id,
        limit=limit,
    )


@router.post(
    "/memory/extract/business",
    response_model=BusinessMemoryExtractResponse,
    tags=["Memory"],
    summary="从业务数据提炼长期记忆关键事件",
    description=(
        "从课程记录和学习记录中提炼长期关键事件。提炼后的结果会写入 memory_events，"
        "并在向量检索可用时同步写入向量索引。适合在业务数据新增或更新后触发。"
    ),
)
def extract_business_memory(
    payload: BusinessMemoryExtractRequest,
    db: Session = Depends(get_db),
) -> BusinessMemoryExtractResponse:
    student = memory_service.get_student(db, payload.student_id, payload.student_code)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="student not found",
        )

    memory_events = memory_service.refresh_business_memory(
        db=db,
        student=student,
    )
    return BusinessMemoryExtractResponse(
        student_id=student.id,
        event_count=len(memory_events),
        memory_events=memory_events,
    )


@router.post(
    "/memory/extract/conversation",
    response_model=ConversationMemoryExtractResponse,
    tags=["Memory"],
    summary="从短期对话提炼长期记忆画像与对话事件",
    description=(
        "从某个学生最近 N 条短期对话中提炼长期用户画像和对话类关键事件。"
        "这个接口不需要手工传对话文本，而是直接从 conversation_memories 里读取。"
    ),
)
def extract_conversation_memory(
    payload: ConversationMemoryExtractRequest,
    db: Session = Depends(get_db),
) -> ConversationMemoryExtractResponse:
    student = student_service.get_student_by_id(db, payload.student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="student not found",
        )

    conversation_texts = memory_service.get_conversation_texts_for_extraction(
        db=db,
        student_id=student.id,
        limit=payload.recent_limit,
    )

    memory_events, user_profile = memory_service.refresh_conversation_memory(
        db=db,
        student=student,
        conversation_texts=conversation_texts,
    )
    return ConversationMemoryExtractResponse(
        student_id=student.id,
        event_count=len(memory_events),
        profile_updated=True,
        memory_events=memory_events,
        user_profile=user_profile,
    )


@router.get(
    "/memory/events",
    response_model=list[MemoryEventRead],
    tags=["Memory"],
    summary="查询长期记忆中的关键事件",
    description=(
        "查询某个学生当前已经沉淀的长期关键事件，包括业务数据提炼出的事件和"
        "短期对话提炼出的事件。"
    ),
)
def list_memory_events(
    student_id: int,
    db: Session = Depends(get_db),
) -> list[MemoryEventRead]:
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="student not found",
        )
    return memory_service.list_memory_events(db, student_id)


@router.post(
    "/memory/search/events",
    response_model=MemoryEventSearchResponse,
    tags=["Memory"],
    summary="混合检索长期记忆关键事件",
    description=(
        "根据用户问题在长期关键事件里做混合检索。系统会同时做关键词匹配和向量检索，"
        "返回最相关的 topN 条事件，并标明每条结果是关键词命中、向量命中还是混合命中。"
    ),
)
def search_memory_events(
    payload: MemoryEventSearchRequest,
    db: Session = Depends(get_db),
) -> MemoryEventSearchResponse:
    student = memory_service.get_student(db, payload.student_id, payload.student_code)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="student not found",
        )

    results = memory_service.search_memory_events(
        db=db,
        student_id=student.id,
        query=payload.query,
        top_n=payload.top_n,
    )
    return MemoryEventSearchResponse(
        student_id=student.id,
        query=payload.query,
        top_n=payload.top_n,
        results=[
            MemoryEventSearchItem(
                **MemoryEventRead.model_validate(item["event"]).model_dump(),
                retrieval_score=item["retrieval_score"],
                retrieval_sources=item["retrieval_sources"],
                retrieval_label=_build_retrieval_label(item["retrieval_sources"]),
                matched_by_keyword="keyword" in item["retrieval_sources"],
                matched_by_vector="vector" in item["retrieval_sources"],
                keyword_score=item.get("keyword_score", 0.0),
                vector_score=item.get("vector_score", 0.0),
            )
            for item in results
        ],
    )


@router.get(
    "/memory/profile",
    response_model=UserProfileRead,
    tags=["Memory"],
    summary="查询长期记忆中的用户画像",
    description=(
        "读取某个学生已经沉淀的长期用户画像，包括画像摘要、沟通风格、偏好主题、"
        "稳定偏好和画像来源。"
    ),
)
def get_user_profile(
    student_id: int,
    db: Session = Depends(get_db),
) -> UserProfileRead:
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="student not found",
        )
    user_profile = memory_service.get_user_profile(db, student_id)
    if user_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user profile not found",
        )
    return user_profile


@router.post(
    "/students",
    response_model=StudentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Students"],
    summary="创建学生",
    description=(
        "创建一条新的学生基础信息。适合录入新学生时使用，内容包括学号、姓名、"
        "联系方式、身份证号等基础资料。"
    ),
)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)) -> StudentRead:
    existing = student_service.get_student_by_code(db, payload.student_code)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="student_code already exists",
        )
    return student_service.create_student(db, payload)


@router.get(
    "/students",
    response_model=list[StudentRead],
    tags=["Students"],
    summary="查询学生列表",
    description="查询当前系统里的学生列表，适合做后台管理、调试和测试数据检查。",
)
def list_students(db: Session = Depends(get_db)) -> list[StudentRead]:
    return student_service.list_students(db)


@router.get(
    "/students/{student_id}",
    response_model=StudentRead,
    tags=["Students"],
    summary="按 ID 查询学生",
    description="按数据库中的 student_id 查询一位学生的基础资料。",
)
def get_student(student_id: int, db: Session = Depends(get_db)) -> StudentRead:
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="student not found")
    return student


@router.put(
    "/students/{student_id}",
    response_model=StudentRead,
    tags=["Students"],
    summary="更新学生信息",
    description="更新某位学生的基础信息，例如手机号、地址、紧急联系人等。",
)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
) -> StudentRead:
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="student not found")
    return student_service.update_student(db, student, payload)


@router.post(
    "/course-records",
    response_model=CourseRecordRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Course Records"],
    summary="创建课程记录",
    description=(
        "创建一条课程记录记录。课程记录主要用于保存评估、学习目标、学习表现、学习背景、学习计划和"
        "教师等信息。"
    ),
)
def create_course_record(
    payload: CourseRecordCreate, db: Session = Depends(get_db)
) -> CourseRecordRead:
    if not course_record_service.student_exists(db, payload.student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="student not found")
    return course_record_service.create_course_record(db, payload)


@router.get(
    "/course-records",
    response_model=list[CourseRecordRead],
    tags=["Course Records"],
    summary="查询课程记录列表",
    description="查询课程记录列表。可以按 student_id 过滤，只看某个学生的课程记录。",
)
def list_course_records(
    student_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
) -> list[CourseRecordRead]:
    return course_record_service.list_course_records(db, student_id=student_id)


@router.get(
    "/course-records/{course_record_id}",
    response_model=CourseRecordRead,
    tags=["Course Records"],
    summary="按 ID 查询课程记录",
    description="按课程记录主键 course_record_id 查询单条课程记录详情。",
)
def get_course_record(course_record_id: int, db: Session = Depends(get_db)) -> CourseRecordRead:
    course_record = course_record_service.get_course_record_by_id(db, course_record_id)
    if course_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="course record not found")
    return course_record


@router.put(
    "/course-records/{course_record_id}",
    response_model=CourseRecordRead,
    tags=["Course Records"],
    summary="更新课程记录",
    description="更新某条课程记录记录，例如修改评估、补充学习目标或调整学习计划。",
)
def update_course_record(
    course_record_id: int,
    payload: CourseRecordUpdate,
    db: Session = Depends(get_db),
) -> CourseRecordRead:
    course_record = course_record_service.get_course_record_by_id(db, course_record_id)
    if course_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="course record not found")
    return course_record_service.update_course_record(db, course_record, payload)


@router.post(
    "/learning-sessions",
    response_model=LearningSessionRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Learning Sessions"],
    summary="创建学习记录",
    description=(
        "创建一条学习记录。学习记录主要保存学习时间、科目、教师、摘要和备注等，"
        "适合记录一次课程或学习过程。"
    ),
)
def create_learning_session(
    payload: LearningSessionCreate, db: Session = Depends(get_db)
) -> LearningSessionRead:
    if not learning_session_service.student_exists(db, payload.student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="student not found")
    return learning_session_service.create_learning_session(db, payload)


@router.get(
    "/learning-sessions",
    response_model=list[LearningSessionRead],
    tags=["Learning Sessions"],
    summary="查询学习记录列表",
    description="查询学习记录列表。可以按 student_id 过滤，只看某个学生的记录。",
)
def list_learning_sessions(
    student_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
) -> list[LearningSessionRead]:
    return learning_session_service.list_learning_sessions(db, student_id=student_id)


@router.get(
    "/learning-sessions/{learning_session_id}",
    response_model=LearningSessionRead,
    tags=["Learning Sessions"],
    summary="按 ID 查询学习记录",
    description="按学习记录主键查询单条学习详情。",
)
def get_learning_session(
    learning_session_id: int,
    db: Session = Depends(get_db),
) -> LearningSessionRead:
    learning_session = learning_session_service.get_learning_session_by_id(db, learning_session_id)
    if learning_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="learning session not found",
        )
    return learning_session


@router.put(
    "/learning-sessions/{learning_session_id}",
    response_model=LearningSessionRead,
    tags=["Learning Sessions"],
    summary="更新学习记录",
    description="更新某条学习记录，例如修改教师、补充备注或调整学习摘要。",
)
def update_learning_session(
    learning_session_id: int,
    payload: LearningSessionUpdate,
    db: Session = Depends(get_db),
) -> LearningSessionRead:
    learning_session = learning_session_service.get_learning_session_by_id(db, learning_session_id)
    if learning_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="learning session not found",
        )
    return learning_session_service.update_learning_session(db, learning_session, payload)
