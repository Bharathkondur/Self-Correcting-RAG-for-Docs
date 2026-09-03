from __future__ import annotations

from langchain_core.documents import Document

from backend.rag_graph import BinaryGrade, build_graph


class FakeRetriever:
    def __init__(self, documents: list[Document]) -> None:
        self.documents = documents
        self.queries: list[str] = []

    def invoke(self, query: str) -> list[Document]:
        self.queries.append(query)
        return self.documents


class FakeServices:
    def __init__(
        self,
        *,
        document_relevant: bool = True,
        grounding_scores: list[str] | None = None,
        answer_scores: list[str] | None = None,
    ) -> None:
        self.document_relevant = document_relevant
        self.grounding_scores = grounding_scores or ["yes"]
        self.answer_scores = answer_scores or ["yes"]
        self.generations = 0
        self.rewrites = 0

    def grade_document(self, question: str, document: Document) -> BinaryGrade:
        score = "yes" if self.document_relevant else "no"
        return BinaryGrade(score=score, reason="deterministic test grade")

    def generate(self, question: str, documents: list[Document], temperature: float) -> str:
        self.generations += 1
        return f"Grounded answer {self.generations} [Source 1]"

    def rewrite(self, original_question: str, current_question: str) -> str:
        self.rewrites += 1
        return f"{original_question} improved {self.rewrites}"

    def grade_grounding(self, documents: list[Document], generation: str) -> BinaryGrade:
        index = min(self.generations - 1, len(self.grounding_scores) - 1)
        return BinaryGrade(score=self.grounding_scores[index], reason="grounding test")

    def grade_answer(self, question: str, generation: str) -> BinaryGrade:
        index = min(self.generations - 1, len(self.answer_scores) - 1)
        return BinaryGrade(score=self.answer_scores[index], reason="relevance test")


def initial_state(question: str = "What is RAG?") -> dict:
    return {
        "original_question": question,
        "question": question,
        "temperature": 0.2,
        "attempt_count": 0,
        "rewrite_count": 0,
        "trace": [],
    }


def test_graph_returns_verified_answer_with_page_source() -> None:
    document = Document(
        page_content="RAG combines retrieval with generation.",
        metadata={"filename": "guide.pdf", "page": 2},
    )
    graph = build_graph(FakeRetriever([document]), services=FakeServices(), max_attempts=3)

    result = graph.invoke(initial_state())

    assert result["status"] == "passed"
    assert result["attempt_count"] == 1
    assert result["sources"][0]["filename"] == "guide.pdf"
    assert result["sources"][0]["page"] == 3
    assert result["trace"][-1]["status"] == "passed"


def test_failed_generation_rewrites_retrieves_and_then_passes() -> None:
    retriever = FakeRetriever([Document(page_content="Relevant facts", metadata={})])
    services = FakeServices(grounding_scores=["no", "yes"])
    graph = build_graph(retriever, services=services, max_attempts=3)

    result = graph.invoke(initial_state("Original question"))

    assert result["status"] == "passed"
    assert result["attempt_count"] == 2
    assert services.rewrites == 1
    assert retriever.queries == ["Original question", "Original question improved 1"]
    assert any(event["status"] == "retrying" for event in result["trace"])


def test_no_context_loop_stops_at_configured_limit() -> None:
    services = FakeServices(document_relevant=False)
    graph = build_graph(FakeRetriever([]), services=services, max_attempts=3)

    result = graph.invoke(initial_state())

    assert result["status"] == "no_context"
    assert result["attempt_count"] == 3
    assert services.rewrites == 2
    assert result["sources"] == []


def test_unverified_answer_is_labeled_best_effort() -> None:
    document = Document(page_content="Some context", metadata={})
    services = FakeServices(grounding_scores=["no"])
    graph = build_graph(FakeRetriever([document]), services=services, max_attempts=2)

    result = graph.invoke(initial_state())

    assert result["status"] == "best_effort"
    assert result["attempt_count"] == 2
    assert result["grounded"] is False
