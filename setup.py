"""
Self-Correcting RAG System
A document-scoped Retrieval-Augmented Generation system with auditable self-correction.
"""

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

with open("backend/requirements.txt", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="self-correcting-rag",
    version="2.0.0",
    author="Bharath Kondur",
    description="Corrective RAG with citations, structured grading, and bounded retries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Bharathkondur/Self-Correcting-RAG-for-Docs",
    packages=find_packages(),
    package_data={"frontend": ["*.html", "*.css", "*.js"]},
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0",
            "flake8>=5.0",
            "mypy>=0.991",
        ],
    },
    entry_points={
        "console_scripts": [
            "rag-serve=backend.app:main",
        ],
    },
    keywords="rag, langchain, ai, nlp, retrieval, generation, self-correction, llm",
    project_urls={
        "Bug Reports": "https://github.com/Bharathkondur/Self-Correcting-RAG-for-Docs/issues",
        "Source": "https://github.com/Bharathkondur/Self-Correcting-RAG-for-Docs",
        "Documentation": "https://github.com/Bharathkondur/Self-Correcting-RAG-for-Docs#readme",
    },
)
