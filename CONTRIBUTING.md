# Contributing to Self-Correcting RAG System

Thank you for your interest in contributing to the Self-Correcting RAG System! This document provides guidelines and instructions for contributing to this project.

## 🎯 How to Contribute

### Reporting Bugs

1. **Check existing issues** first to avoid duplicates
2. **Use the bug report template** when creating new issues
3. **Provide detailed information** including:
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Error logs/screenshots

### Suggesting Features

1. **Check the roadmap** in README.md first
2. **Open a feature request** with:
   - Clear description of the feature
   - Use cases and benefits
   - Possible implementation approach

### Pull Request Process

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** following our coding standards
4. **Add tests** for new functionality
5. **Update documentation** if needed
6. **Run the test suite**: `python -m pytest`
7. **Submit a pull request**

## 🛠️ Development Setup

### Local Development

```bash
# Clone your fork
git clone https://github.com/yourusername/self-correcting-rag.git
cd self-correcting-rag

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
pip install -r requirements-dev.txt

# Copy environment file
cp backend/.env.example backend/.env
# Edit .env with your API keys
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=backend

# Run specific test file
python -m pytest tests/test_rag_graph.py
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code
black backend/

# Lint code
flake8 backend/

# Type checking
mypy backend/

# Run all checks
pre-commit run --all-files
```

## 📋 Coding Standards

### Python Style Guide

- Follow **PEP 8** conventions
- Use **type hints** for all function signatures
- Write **docstrings** for all public functions/classes
- Keep line length under **88 characters** (Black default)

### Code Structure

```python
"""
Module docstring describing purpose.
"""

from typing import Dict, List, Optional
import logging

# Local imports last
from .utils import helper_function

logger = logging.getLogger(__name__)


class ExampleClass:
    """Class docstring with purpose and usage."""
    
    def __init__(self, param: str) -> None:
        """Initialize with clear parameter description."""
        self.param = param
    
    def public_method(self, data: Dict[str, str]) -> Optional[str]:
        """
        Public method with full docstring.
        
        Args:
            data: Description of the parameter
            
        Returns:
            Description of return value
            
        Raises:
            ValueError: When data is invalid
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        return self._private_method(data)
    
    def _private_method(self, data: Dict[str, str]) -> str:
        """Private method with brief description."""
        # Implementation
        pass
```

### Commit Messages

Use **conventional commits** format:

```
type(scope): description

feat(api): add new endpoint for document analysis
fix(rag): resolve hallucination detection bug  
docs(readme): update installation instructions
test(graph): add tests for self-correction loop
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## 🧪 Testing Guidelines

### Test Structure

```python
"""Tests for rag_graph module."""

import pytest
from unittest.mock import Mock, patch

from backend.rag_graph import build_graph


class TestRagGraph:
    """Test cases for RAG graph functionality."""
    
    def test_build_graph_success(self):
        """Test successful graph building."""
        # Arrange
        mock_retriever = Mock()
        
        # Act
        graph = build_graph(mock_retriever)
        
        # Assert
        assert graph is not None
        assert callable(graph.invoke)
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async operations."""
        # Test implementation
        pass
```

### Test Coverage

- Aim for **90%+ coverage** on new code
- Test both **happy path** and **error cases**  
- Include **integration tests** for API endpoints
- Add **performance tests** for critical paths

## 📚 Documentation

### Docstring Format

Use **Google style** docstrings:

```python
def process_document(file_path: str, chunk_size: int = 300) -> List[str]:
    """
    Process a document into chunks for RAG ingestion.
    
    This function loads a PDF document, splits it into semantic chunks,
    and prepares them for embedding and storage.
    
    Args:
        file_path: Path to the PDF file to process
        chunk_size: Maximum size of each chunk in tokens
        
    Returns:
        List of text chunks ready for embedding
        
    Raises:
        FileNotFoundError: If the specified file doesn't exist
        ValueError: If chunk_size is less than 50
        
    Example:
        >>> chunks = process_document("document.pdf", chunk_size=500)
        >>> len(chunks)
        25
    """
```

### README Updates

When adding new features:

1. Update the **Features** section
2. Add to **Quick Start** if needed
3. Update **Configuration** section
4. Add to **Roadmap** if incomplete

## 🔍 Code Review Process

### For Reviewers

- Check **code quality** and adherence to standards
- Verify **test coverage** and test quality  
- Review **documentation** completeness
- Test **functionality** manually if needed
- Provide **constructive feedback**

### For Contributors

- Respond to feedback **promptly** and **professionally**
- Make **focused commits** addressing specific feedback
- **Test thoroughly** before requesting re-review
- **Update documentation** when requested

## 🎖️ Recognition

Contributors will be:

- **Listed in CONTRIBUTORS.md** 
- **Mentioned in release notes**
- **Tagged in social media** announcements (with permission)

## ❓ Questions?

- **Open a discussion** for general questions
- **Join our community** (if applicable)
- **Email maintainers** for sensitive issues

---

Thank you for helping make this project better! 🚀