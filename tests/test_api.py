from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient
from langchain_core.documents import Document
from reportlab.pdfgen import canvas

from backend.app import FaissRetriever, create_app, process_pdf


class FakeGraph:
    def invoke(self, state: dict) -> dict:
        return {
            **state,
            "generation": "A supported answer [Source 1]",
            "status": "passed",
            "attempt_count": 1,
            "trace": [{"step": "finalize", "status": "passed", "detail": "Answer verified."}],
            "sources": [{"id": 1, "filename": "sample.pdf", "page": 1, "snippet": "Evidence"}],
        }


class FakeEmbeddings:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, float(index)] for index, _ in enumerate(texts, start=1)]

    def embed_query(self, query: str) -> list[float]:
        return [1.0, 1.0]


def test_faiss_retriever_returns_nearest_document() -> None:
    documents = [Document(page_content="first"), Document(page_content="second")]
    retriever = FaissRetriever(documents, FakeEmbeddings(), k=1)

    assert retriever.invoke("query") == [documents[0]]


def test_real_pdf_ingestion_builds_searchable_graph(tmp_path) -> None:
    pdf_path = tmp_path / "guide.pdf"
    pdf = canvas.Canvas(str(pdf_path))
    pdf.drawString(72, 720, "Retrieval augmented generation uses external evidence.")
    pdf.save()

    with patch("backend.app.get_embeddings", return_value=FakeEmbeddings()):
        graph, chunk_count = process_pdf(pdf_path, "guide.pdf")

    assert chunk_count == 1
    assert callable(graph.invoke)


def test_health_endpoint() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_upload_creates_isolated_session_and_chat_uses_it() -> None:
    app = create_app()
    with (
        patch("backend.app.process_pdf", return_value=(FakeGraph(), 7)),
        TestClient(app) as client,
    ):
        upload = client.post(
            "/api/documents",
            files={"file": ("sample.pdf", b"%PDF-1.4\nmock", "application/pdf")},
        )
        assert upload.status_code == 201
        payload = upload.json()
        assert payload["chunk_count"] == 7

        chat = client.post(
            "/api/chat",
            json={
                "session_id": payload["session_id"],
                "question": "What does it say?",
                "temperature": 0.3,
            },
        )
    assert chat.status_code == 200
    assert chat.json()["status"] == "passed"
    assert chat.json()["sources"][0]["page"] == 1


def test_two_uploads_receive_different_sessions() -> None:
    app = create_app()
    with (
        patch("backend.app.process_pdf", return_value=(FakeGraph(), 1)),
        TestClient(app) as client,
    ):
        first = client.post(
            "/api/documents", files={"file": ("one.pdf", b"%PDF-one", "application/pdf")}
        )
        second = client.post(
            "/api/documents", files={"file": ("two.pdf", b"%PDF-two", "application/pdf")}
        )
    assert first.json()["session_id"] != second.json()["session_id"]


def test_rejects_non_pdf_and_missing_session() -> None:
    with TestClient(create_app()) as client:
        bad_upload = client.post(
            "/api/documents", files={"file": ("notes.txt", b"hello", "text/plain")}
        )
        fake_pdf = client.post(
            "/api/documents",
            files={"file": ("fake.pdf", b"not really a pdf", "application/pdf")},
        )
        missing = client.post(
            "/api/chat",
            json={
                "session_id": "00000000-0000-0000-0000-000000000000",
                "question": "What does it say?",
            },
        )
    assert bad_upload.status_code == 415
    assert fake_pdf.status_code == 415
    assert missing.status_code == 404


def test_delete_session_prevents_future_chat() -> None:
    app = create_app()
    with (
        patch("backend.app.process_pdf", return_value=(FakeGraph(), 1)),
        TestClient(app) as client,
    ):
        upload = client.post(
            "/api/documents",
            files={"file": ("sample.pdf", b"%PDF-mock", "application/pdf")},
        )
        session_id = upload.json()["session_id"]
        deleted = client.delete(f"/api/documents/{session_id}")
        chat = client.post(
            "/api/chat",
            json={"session_id": session_id, "question": "Is it still available?"},
        )

    assert deleted.status_code == 204
    assert chat.status_code == 404
