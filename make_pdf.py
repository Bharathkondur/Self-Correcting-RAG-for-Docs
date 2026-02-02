#!/usr/bin/env python3
"""
Test PDF Generator for RAG System Demo

This script generates a sample PDF document for testing the RAG system.
The generated PDF contains information about artificial intelligence and
machine learning concepts to demonstrate the system's capabilities.
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import os


def create_test_pdf(filename: str = "test.pdf") -> str:
    """
    Create a test PDF document with AI/ML content for RAG system testing.
    
    Args:
        filename: Name of the PDF file to create
        
    Returns:
        Path to the created PDF file
    """
    
    # Create document with proper formatting
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("Artificial Intelligence and Machine Learning Overview", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Introduction
    intro = """
    Artificial Intelligence (AI) represents one of the most significant technological 
    advancements of our time. This document provides an overview of key concepts, 
    applications, and future directions in the field of AI and Machine Learning.
    """
    story.append(Paragraph(intro, styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Main content sections
    sections = [
        {
            "title": "What is Artificial Intelligence?",
            "content": """
            Artificial Intelligence refers to the simulation of human intelligence in machines 
            that are programmed to think and learn like humans. AI systems can perform tasks 
            that typically require human intelligence, such as visual perception, speech 
            recognition, decision-making, and language translation.
            """
        },
        {
            "title": "Machine Learning Fundamentals",
            "content": """
            Machine Learning is a subset of AI that enables computers to learn and improve 
            from experience without being explicitly programmed. There are three main types: 
            supervised learning (learning from labeled data), unsupervised learning (finding 
            patterns in unlabeled data), and reinforcement learning (learning through 
            interaction with an environment).
            """
        },
        {
            "title": "Natural Language Processing",
            "content": """
            Natural Language Processing (NLP) is a branch of AI that helps computers understand, 
            interpret, and manipulate human language. Modern NLP applications include chatbots, 
            language translation, sentiment analysis, and document summarization. Large Language 
            Models (LLMs) like GPT have revolutionized this field.
            """
        },
        {
            "title": "Retrieval-Augmented Generation (RAG)",
            "content": """
            Retrieval-Augmented Generation combines the power of large language models with 
            external knowledge retrieval. RAG systems first retrieve relevant information from 
            a knowledge base, then use this context to generate more accurate and factual responses. 
            This approach helps address the limitation of knowledge cutoffs in language models.
            """
        },
        {
            "title": "Applications and Future Directions",
            "content": """
            AI applications span numerous industries including healthcare (medical diagnosis), 
            finance (fraud detection), transportation (autonomous vehicles), and education 
            (personalized learning). Future developments focus on making AI more interpretable, 
            ethical, and beneficial for humanity while addressing challenges like bias and safety.
            """
        },
        {
            "title": "Technical Implementation Considerations",
            "content": """
            Implementing AI systems requires careful consideration of data quality, model selection, 
            computational resources, and evaluation metrics. Key technical requirements include 
            sufficient training data, appropriate hardware (GPUs/TPUs for deep learning), 
            robust evaluation frameworks, and continuous monitoring for performance and bias.
            """
        }
    ]
    
    # Add sections to the document
    for section in sections:
        # Section title
        title_para = Paragraph(section["title"], styles['Heading2'])
        story.append(title_para)
        story.append(Spacer(1, 10))
        
        # Section content
        content_para = Paragraph(section["content"], styles['Normal'])
        story.append(content_para)
        story.append(Spacer(1, 15))
    
    # Conclusion
    conclusion = """
    This document provides a foundation for understanding AI and ML concepts. The field 
    continues to evolve rapidly, with new breakthroughs in areas like transformer architectures, 
    multimodal AI, and AI safety research. As these technologies mature, they promise to 
    transform how we work, communicate, and solve complex problems.
    """
    story.append(Paragraph("Conclusion", styles['Heading2']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(conclusion, styles['Normal']))
    
    # Build the PDF
    doc.build(story)
    
    # Get absolute path
    abs_path = os.path.abspath(filename)
    print(f"✅ Test PDF created successfully: {abs_path}")
    return abs_path


if __name__ == "__main__":
    create_test_pdf("test.pdf")
