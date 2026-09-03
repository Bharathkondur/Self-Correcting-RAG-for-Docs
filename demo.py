#!/usr/bin/env python3
"""Exercise the public API with the included sample PDF."""

from __future__ import annotations

import asyncio
from pathlib import Path

import aiohttp

from make_pdf import create_test_pdf

BASE_URL = "http://localhost:8000"


async def upload_document(session: aiohttp.ClientSession, file_path: Path) -> str | None:
    print(f"📄 Uploading document: {file_path}")
    with file_path.open("rb") as pdf_file:
        data = aiohttp.FormData()
        data.add_field("file", pdf_file, filename=file_path.name, content_type="application/pdf")
        async with session.post(f"{BASE_URL}/api/documents", data=data) as response:
            result = await response.json()
            if response.status == 201:
                print(f"✅ Indexed {result['chunk_count']} chunks in an isolated session")
                return result["session_id"]
            print(f"❌ Upload failed: {result}")
            return None


async def ask_question(
    session: aiohttp.ClientSession,
    session_id: str,
    question: str,
) -> None:
    print(f"\n💭 {question}")
    async with session.post(
        f"{BASE_URL}/api/chat",
        json={"session_id": session_id, "question": question, "temperature": 0.2},
    ) as response:
        result = await response.json()
        if response.status != 200:
            print(f"❌ Question failed: {result}")
            return
        print(f"🤖 {result['answer']}")
        print(f"🔎 Status: {result['status']} · attempts: {result['attempts']}")
        for source in result["sources"]:
            page = f" page {source['page']}" if source["page"] else ""
            print(f"   [Source {source['id']}] {source['filename']}{page}")


async def run_demo() -> None:
    test_pdf = Path("test.pdf")
    if not test_pdf.exists():
        create_test_pdf(str(test_pdf))

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/api/health") as health:
            if health.status != 200:
                raise RuntimeError(f"API health check returned {health.status}")

        session_id = await upload_document(session, test_pdf)
        if session_id is None:
            return
        questions = [
            "What are the three main types of machine learning?",
            "How does retrieval-augmented generation work?",
            "What technical considerations are mentioned?",
        ]
        for question in questions:
            await ask_question(session, session_id, question)
        await session.delete(f"{BASE_URL}/api/documents/{session_id}")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except (aiohttp.ClientError, RuntimeError) as exc:
        print(f"❌ Demo failed: {exc}")
        print("Start the server first with: python -m backend.app")
