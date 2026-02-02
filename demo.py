#!/usr/bin/env python3
"""
Demo script for Self-Correcting RAG System
This script demonstrates how to use the RAG system programmatically.
"""

import asyncio
import aiohttp
import json
import os
from pathlib import Path

# Base URL for the API
BASE_URL = "http://localhost:8000"

async def upload_document(session, file_path: str):
    """Upload a PDF document to the RAG system."""
    print(f"📄 Uploading document: {file_path}")
    
    with open(file_path, 'rb') as f:
        data = aiohttp.FormData()
        data.add_field('file', f, filename=os.path.basename(file_path))
        
        async with session.post(f"{BASE_URL}/upload", data=data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Upload successful! Processed {result['count']} chunks")
                return True
            else:
                error = await response.text()
                print(f"❌ Upload failed: {error}")
                return False

async def ask_question(session, question: str, temperature: float = 0.5):
    """Ask a question to the RAG system."""
    print(f"\n💭 Asking: {question}")
    
    payload = {
        "question": question,
        "temperature": temperature
    }
    
    async with session.post(f"{BASE_URL}/chat", json=payload) as response:
        if response.status == 200:
            result = await response.json()
            print(f"🤖 Answer: {result['answer']}")
            if result.get('final_question') != question:
                print(f"🔄 Query was rewritten to: {result['final_question']}")
            return result
        else:
            error = await response.text()
            print(f"❌ Question failed: {error}")
            return None

async def demo_conversation():
    """Demonstrate a full conversation with the RAG system."""
    
    # Sample questions to demonstrate capabilities
    questions = [
        "What is the main topic of this document?",
        "Can you summarize the key points?",
        "What specific details are mentioned about implementation?",
        "Are there any technical requirements mentioned?",
        "What conclusions can be drawn from this document?"
    ]
    
    print("🎯 Starting interactive demo session...")
    
    async with aiohttp.ClientSession() as session:
        # First, check if we have a test document
        test_pdf = "test.pdf"
        if not os.path.exists(test_pdf):
            print("📝 Creating test document...")
            # Import and run the PDF creation script
            import sys
            sys.path.append('.')
            import make_pdf
            print(f"✅ Test document created: {test_pdf}")
        
        # Upload the document
        success = await upload_document(session, test_pdf)
        if not success:
            print("❌ Failed to upload document. Make sure the server is running!")
            return
        
        print("\n" + "="*60)
        print("🚀 RAG SYSTEM DEMO - Self-Correcting Capabilities")
        print("="*60)
        
        # Ask demo questions
        for i, question in enumerate(questions, 1):
            print(f"\n📍 Question {i}/{len(questions)}")
            await ask_question(session, question)
            
            # Small delay for readability
            await asyncio.sleep(1)
        
        print("\n" + "="*60)
        print("🎉 Demo completed! Try asking your own questions via the web interface.")
        print(f"🌐 Open your browser to: {BASE_URL}")
        print("="*60)

async def health_check():
    """Check if the RAG system is running."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/") as response:
                if response.status == 200:
                    print("✅ RAG system is running!")
                    return True
                else:
                    print(f"❌ RAG system returned status: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Cannot connect to RAG system: {e}")
        print("💡 Make sure to start the server with: python backend/app.py")
        return False

def print_startup_info():
    """Print information about starting the system."""
    print("🧠 Self-Correcting RAG System Demo")
    print("=" * 40)
    print()
    print("Before running this demo:")
    print("1. Start the server: python backend/app.py")
    print("2. Make sure you have set OPENAI_API_KEY in backend/.env")
    print("   Or install Ollama with: ollama pull mistral && ollama pull nomic-embed-text")
    print()

if __name__ == "__main__":
    print_startup_info()
    
    # Run the demo
    try:
        # First check if server is running
        if not asyncio.run(health_check()):
            exit(1)
        
        # Run the full demo
        asyncio.run(demo_conversation())
        
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")