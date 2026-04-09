# @XobierWang

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {
        "env_file": Path(__file__).resolve().parent.parent / ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    qwen_api_key: str = ""
    qwen_model: str = "qwen-vl-plus-latest"
    qwen_tts_model: str = "cosyvoice-v3-flash"
    qwen_tts_voice: str = "longanyang"
    qwen_embedding_model: str = "text-embedding-v4"
    qwen_embedding_dimensions: int = 1024
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"


settings = Settings()
