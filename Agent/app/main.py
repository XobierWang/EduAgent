# @XobierWang

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.db.init_db import init_db
from app.db.session import DATA_DIR
init_db()
STATIC_DIR = Path(__file__).resolve().parent / "static"

openapi_tags = [
    {
        "name": "Agent",
        "description": "通过 Qwen 大模型结合内部工具进行信息查询。",
    },
    {
        "name": "Students",
        "description": "学生基础身份信息的创建、读取和更新。",
    },
    {
        "name": "Course Records",
        "description": "学生课程记录信息的创建、读取和更新。",
    },
    {
        "name": "Learning Sessions",
        "description": "学生学习记录的创建、读取和更新。",
    },
    {
        "name": "Memory",
        "description": "长期记忆偏好配置的查询与更新。",
    },
]

app = FastAPI(
    title="EduAgent API",
    version="0.1.0",
    description="学生信息、课程记录和学习记录的基础数据服务。",
    openapi_tags=openapi_tags,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/media", StaticFiles(directory=DATA_DIR), name="media")
app.include_router(router, prefix="/api")


@app.get("/", include_in_schema=False)
def read_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/query", include_in_schema=False)
def read_query_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/chat", include_in_schema=False)
def read_chat_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "chat.html")
