"""FastAPI entry point for the document-scoped corrective-RAG application."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Annotated, Any, Literal

import faiss
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from backend.config import PROJECT_ROOT, get_settings
from backend.logging_config import setup_logging
from backend.rag_graph import TraceEvent, build_graph
from backend.session_store import SessionStore

try:
    from langchain_ollama import OllamaEmbeddings
except ImportError:  # pragma: no cover - exercised only in optional local mode
    OllamaEmbeddings = None


settings = get_settings()
setup_logging(log_level=settings.log_level, log_file=os.getenv("LOG_FILE"))
logger = logging.getLogger(__name__)


class UploadResponse(BaseModel):
    session_id: str
    filename: str
    chunk_count: int
    message: str


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=36, max_length=36)
    question: str = Field(min_length=2, max_length=2_000)
    temperature: float = Field(default=0.2, ge=0, le=1)


class SourceResponse(BaseModel):
    id: int
    filename: str
    page: int | None
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    status: Literal["passed", "best_effort", "no_context"]
    final_question: str
    attempts: int
    trace: list[TraceEvent]
    sources: list[SourceResponse]


class FaissRetriever:
    """Minimal cosine-similarity retriever over a document list."""

    def __init__(self, documents: list[Document], embeddings: Any, k: int = 4) -> None:
        self._documents = documents
        self._embeddings = embeddings
        self._k = min(k, len(documents))
        vectors = np.asarray(
            embeddings.embed_documents([document.page_content for document in documents]),
            dtype=np.float32,
        )
        if vectors.ndim != 2 or vectors.shape[0] != len(documents):
            raise ValueError("Embedding provider returned an unexpected vector shape.")
        faiss.normalize_L2(vectors)
        self._index = faiss.IndexFlatIP(vectors.shape[1])
        self._index.add(vectors)

    def invoke(self, query: str) -> list[Document]:
        vector = np.asarray([self._embeddings.embed_query(query)], dtype=np.float32)
        faiss.normalize_L2(vector)
        _, indices = self._index.search(vector, self._k)
        return [self._documents[index] for index in indices[0] if index >= 0]


def get_embeddings() -> Any:
    """Return an explicitly configured embedding provider."""

    if os.getenv("OPENAI_API_KEY"):
        logger.info("Using OpenAI embeddings: %s", settings.embedding_model)
        return OpenAIEmbeddings(model=settings.embedding_model)
    if OllamaEmbeddings is None:
        raise RuntimeError(
            "Local embeddings require langchain-ollama. Install the project dependencies "
            "or configure OPENAI_API_KEY."
        )
    logger.info("Using Ollama embeddings: %s", settings.ollama_embedding_model)
    return OllamaEmbeddings(
        model=settings.ollama_embedding_model,
        base_url=settings.ollama_base_url,
    )


def process_pdf(file_path: Path, display_name: str) -> tuple[Any, int]:
    """Load, chunk, embed, and compile a graph for one PDF."""

    reader = PdfReader(str(file_path))
    documents = [
        Document(
            page_content=page.extract_text() or "",
            metadata={"filename": display_name, "page": page_number},
        )
        for page_number, page in enumerate(reader.pages)
    ]
    if not documents or not any(document.page_content.strip() for document in documents):
        raise ValueError("The PDF does not contain extractable text.")

    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = [chunk for chunk in splitter.split_documents(documents) if chunk.page_content.strip()]
    if not chunks:
        raise ValueError("The PDF did not produce any searchable text chunks.")

    retriever = FaissRetriever(chunks, get_embeddings(), settings.retrieval_k)
    return build_graph(retriever, max_attempts=settings.max_attempts), len(chunks)


def create_app() -> FastAPI:
    application = FastAPI(
        title="Self-Correcting RAG for Docs",
        version="2.0.0",
        description="Document-scoped corrective RAG with citations and auditable grading.",
    )
    application.state.sessions = SessionStore(settings.session_ttl_seconds)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @application.get("/api/health")
    async def health() -> dict[str, str]:
        provider = "openai" if os.getenv("OPENAI_API_KEY") else "ollama"
        return {"status": "healthy", "provider": provider, "version": "2.0.0"}

    @application.post("/api/documents", response_model=UploadResponse, status_code=201)
    async def upload_document(
        file: Annotated[UploadFile, File(description="A text-based PDF, up to MAX_UPLOAD_MB")],
    ) -> UploadResponse:
        filename = Path(file.filename or "document.pdf").name
        if Path(filename).suffix.lower() != ".pdf":
            raise HTTPException(status_code=415, detail="Only PDF files are supported.")

        contents = await file.read(settings.max_upload_bytes + 1)
        await file.close()
        if len(contents) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"PDF exceeds the {settings.max_upload_bytes // (1024 * 1024)} MB limit.",
            )
        if not contents.startswith(b"%PDF-"):
            raise HTTPException(status_code=415, detail="The uploaded file is not a valid PDF.")

        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temporary_file:
                temporary_file.write(contents)
                temporary_path = Path(temporary_file.name)
            graph, chunk_count = await run_in_threadpool(process_pdf, temporary_path, filename)
            session = application.state.sessions.create(
                filename=filename,
                graph=graph,
                chunk_count=chunk_count,
            )
            logger.info(
                "Indexed document session=%s filename=%s chunks=%d",
                session.session_id,
                filename,
                chunk_count,
            )
            return UploadResponse(
                session_id=session.session_id,
                filename=filename,
                chunk_count=chunk_count,
                message="Document processed and isolated in a new session.",
            )
        except (ValueError, PdfReadError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Document processing failed for %s", filename)
            raise HTTPException(
                status_code=500,
                detail="Document processing failed. Check the server logs for details.",
            ) from exc
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    @application.post("/api/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse:
        session = application.state.sessions.get(request.session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Document session not found or expired. Upload the PDF again.",
            )

        initial_state = {
            "original_question": request.question,
            "question": request.question,
            "temperature": request.temperature,
            "attempt_count": 0,
            "rewrite_count": 0,
            "trace": [],
        }
        try:
            result = await run_in_threadpool(session.graph.invoke, initial_state)
        except Exception as exc:
            logger.exception("RAG execution failed for session=%s", request.session_id)
            raise HTTPException(
                status_code=500,
                detail="Answer generation failed. Check the server logs for details.",
            ) from exc

        return ChatResponse(
            answer=result["generation"],
            status=result["status"],
            final_question=result.get("question", request.question),
            attempts=result.get("attempt_count", 1),
            trace=result.get("trace", []),
            sources=result.get("sources", []),
        )

    @application.delete("/api/documents/{session_id}", status_code=204)
    async def delete_document(session_id: str) -> None:
        if not application.state.sessions.delete(session_id):
            raise HTTPException(status_code=404, detail="Document session not found.")

    frontend_path = PROJECT_ROOT / "frontend"
    application.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
    return application


app = create_app()


def main() -> None:
    """Run the development server from the installed console command."""

    import uvicorn

    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
