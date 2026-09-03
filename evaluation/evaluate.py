"""Run a small, reproducible quality and latency evaluation against the live API."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import httpx


def percentile_95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--pdf", type=Path, default=Path("test.pdf"))
    parser.add_argument("--dataset", type=Path, default=Path("evaluation/dataset.json"))
    args = parser.parse_args()

    cases = json.loads(args.dataset.read_text(encoding="utf-8"))
    with httpx.Client(base_url=args.base_url, timeout=120) as client:
        with args.pdf.open("rb") as pdf_file:
            response = client.post(
                "/api/documents",
                files={"file": (args.pdf.name, pdf_file, "application/pdf")},
            )
        response.raise_for_status()
        session_id = response.json()["session_id"]

        results: list[dict] = []
        for case in cases:
            started = time.perf_counter()
            answer_response = client.post(
                "/api/chat",
                json={"session_id": session_id, "question": case["question"]},
            )
            latency = time.perf_counter() - started
            answer_response.raise_for_status()
            payload = answer_response.json()
            answer_lower = payload["answer"].lower()
            terms = case.get("expected_terms", [])
            term_recall = (
                sum(term.lower() in answer_lower for term in terms) / len(terms) if terms else 1.0
            )
            expected_page = case.get("expected_page")
            page_hit = expected_page is None or any(
                source.get("page") == expected_page for source in payload["sources"]
            )
            status_hit = payload["status"] == case.get("expected_status", "passed")
            result = {
                "question": case["question"],
                "status": payload["status"],
                "status_match": status_hit,
                "term_recall": round(term_recall, 3),
                "citation_page_match": page_hit,
                "latency_seconds": round(latency, 3),
                "attempts": payload["attempts"],
            }
            results.append(result)
            print(json.dumps(result))

        client.delete(f"/api/documents/{session_id}")

    latencies = [result["latency_seconds"] for result in results]
    summary = {
        "cases": len(results),
        "status_accuracy": round(
            sum(result["status_match"] for result in results) / len(results), 3
        ),
        "mean_term_recall": round(statistics.mean(result["term_recall"] for result in results), 3),
        "citation_page_accuracy": round(
            sum(result["citation_page_match"] for result in results) / len(results), 3
        ),
        "mean_latency_seconds": round(statistics.mean(latencies), 3),
        "p95_latency_seconds": round(percentile_95(latencies), 3),
    }
    print("\nSummary")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
