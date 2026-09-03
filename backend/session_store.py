"""Thread-safe, expiring storage for document-specific RAG sessions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class DocumentSession:
    session_id: str
    filename: str
    graph: Any
    chunk_count: int
    created_at: datetime


class SessionStore:
    """Small in-memory store suitable for a single demo process.

    A production deployment can replace this class with Redis/object storage
    without changing the HTTP API.
    """

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._ttl = timedelta(seconds=ttl_seconds)
        self._sessions: dict[str, DocumentSession] = {}
        self._lock = RLock()

    def create(self, *, filename: str, graph: Any, chunk_count: int) -> DocumentSession:
        now = datetime.now(UTC)
        session = DocumentSession(
            session_id=str(uuid4()),
            filename=filename,
            graph=graph,
            chunk_count=chunk_count,
            created_at=now,
        )
        with self._lock:
            self._purge_expired(now)
            self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> DocumentSession | None:
        now = datetime.now(UTC)
        with self._lock:
            self._purge_expired(now)
            return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def _purge_expired(self, now: datetime) -> None:
        expired = [
            key for key, session in self._sessions.items() if now - session.created_at > self._ttl
        ]
        for key in expired:
            del self._sessions[key]
