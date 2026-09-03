"""Environment-backed application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / "backend" / ".env")


def _csv(name: str, default: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in os.getenv(name, default).split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    answer_model: str
    grader_model: str
    embedding_model: str
    ollama_chat_model: str
    ollama_embedding_model: str
    ollama_base_url: str
    max_attempts: int
    max_upload_bytes: int
    session_ttl_seconds: int
    retrieval_k: int
    chunk_size: int
    chunk_overlap: int
    cors_origins: tuple[str, ...]
    log_level: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        answer_model=os.getenv("ANSWER_MODEL", "gpt-4o-mini"),
        grader_model=os.getenv("GRADER_MODEL", "gpt-4o-mini"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        ollama_chat_model=os.getenv("OLLAMA_CHAT_MODEL", "mistral"),
        ollama_embedding_model=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        max_attempts=max(1, int(os.getenv("MAX_ATTEMPTS", "3"))),
        max_upload_bytes=max(1, int(os.getenv("MAX_UPLOAD_MB", "20"))) * 1024 * 1024,
        session_ttl_seconds=max(60, int(os.getenv("SESSION_TTL_SECONDS", "3600"))),
        retrieval_k=max(1, int(os.getenv("RETRIEVAL_K", "4"))),
        chunk_size=max(100, int(os.getenv("CHUNK_SIZE", "500"))),
        chunk_overlap=max(0, int(os.getenv("CHUNK_OVERLAP", "75"))),
        cors_origins=_csv("CORS_ORIGINS", "http://localhost:8000"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
