# @XobierWang

from typing import Optional

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "The MCP server requires the `mcp` package and Python 3.10+. "
        "Your current environment cannot import it."
    ) from exc

from app.db.session import SessionLocal
from app.services import mcp_tool_service


mcp = FastMCP("edu-agent-mcp-server")


@mcp.tool()
def verify_student_identity(
    student_code: str,
    phone: Optional[str] = None,
    id_number: Optional[str] = None,
) -> dict:
    """
    校验学生身份。
    可使用 student_code + phone 或 student_code + id_number 进行验证。
    """
    db = SessionLocal()
    try:
        return mcp_tool_service.verify_student(
            db,
            student_code=student_code,
            phone=phone,
            id_number=id_number,
        )
    finally:
        db.close()


@mcp.tool()
def get_student_profile(
    student_id: Optional[int] = None,
    student_code: Optional[str] = None,
) -> dict:
    """
    查询学生基础信息。
    student_id 和 student_code 二选一。
    """
    db = SessionLocal()
    try:
        return mcp_tool_service.get_student_profile(
            db,
            student_id=student_id,
            student_code=student_code,
        )
    finally:
        db.close()


@mcp.tool()
def get_student_course_records(
    student_id: Optional[int] = None,
    student_code: Optional[str] = None,
) -> dict:
    """
    查询学生课程记录信息。
    student_id 和 student_code 二选一。
    """
    db = SessionLocal()
    try:
        return mcp_tool_service.get_student_course_records(
            db,
            student_id=student_id,
            student_code=student_code,
        )
    finally:
        db.close()


@mcp.tool()
def get_student_learning_sessions(
    student_id: Optional[int] = None,
    student_code: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """
    查询学生学习记录。
    student_id 和 student_code 二选一。
    如果只查最近一次记录，传 limit=1。
    """
    db = SessionLocal()
    try:
        return mcp_tool_service.get_student_learning_sessions(
            db,
            student_id=student_id,
            student_code=student_code,
            limit=limit,
        )
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run()
