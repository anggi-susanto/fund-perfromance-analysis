# Test Suite

This directory contains all tests for the Fund Performance Analysis system.

## Directory Structure

```
tests/
├── test_integration.py      # Main integration test suite (run this!)
├── unit/                     # Unit tests for individual components
│   └── test_table_parser.py # Table parsing logic tests
├── api/                      # API endpoint tests
│   └── (future tests)
├── manual/                   # Manual test scripts for debugging
│   ├── test_llm_setup.py           # Verify LLM configuration
│   ├── test_pdf_tables.py          # Test PDF table extraction
│   └── test_concurrent_requests.py # Test concurrent API requests
└── deprecated/               # Old test scripts (kept for reference)
    ├── test_upload.py
    ├── test_rag_queries.py
    └── ... (other old tests)
```

## Main Integration Test

### `test_integration.py` ⭐
**The primary test suite** - validates the entire system flow:
1. Backend Health Check
2. Document Upload
3. Document Processing
4. Chat Query & Vector Search (RAG)
5. Frontend Accessibility
6. API Endpoints

**Run this test to verify the system is working:**
```bash
python3 tests/test_integration.py
```

Expected output: **6/6 tests passed (100%)** ✅

## Unit Tests

### `unit/test_table_parser.py`
Tests the table parsing logic in isolation:
- Capital call table parsing
- Distribution table parsing
- Adjustment table parsing
- Table classification

```bash
# Run from backend container
docker compose exec backend python tests/unit/test_table_parser.py
```

## Manual Test Scripts

These scripts are for manual testing during development:

### `manual/test_llm_setup.py`
Verify LLM and embeddings configuration:
```bash
docker compose exec backend python tests/manual/test_llm_setup.py
```

### `manual/test_pdf_tables.py`
Test PDF table extraction with pdfplumber:
```bash
cd files && python3 ../tests/manual/test_pdf_tables.py
```

### `manual/test_concurrent_requests.py`
Test multiple concurrent chat requests:
```bash
python3 tests/manual/test_concurrent_requests.py
```

## Running All Tests

### Integration Tests (Recommended)
```bash
python3 tests/test_integration.py
```

### Unit Tests with pytest
```bash
pytest tests/unit/ -v
```

### All Tests (when more are added)
```bash
pytest tests/ -v --ignore=tests/deprecated --ignore=tests/manual
```

## Test Requirements

**Prerequisites:**
- Backend running on http://localhost:8000
- Frontend running on http://localhost:3000
- PostgreSQL with pgvector extension
- Sample PDF file in `files/Sample_Fund_Performance_Report.pdf`

**Environment:**
- Python 3.11+
- Docker and Docker Compose
- Valid API keys in `.env` (Groq, etc.)

## Test Coverage

Current test coverage includes:
- ✅ Document upload and processing
- ✅ Vector embeddings and similarity search
- ✅ RAG chat queries with context retrieval
- ✅ Frontend page accessibility
- ✅ API endpoints functionality
- ✅ Error handling and status reporting
- ✅ Table parsing and classification
- ✅ LLM integration

## Deprecated Tests

The `deprecated/` folder contains older test scripts that have been superseded by `test_integration.py`. These are kept for reference but may not work with the current system:

- `test_upload.py` - Old upload test (use test_integration.py instead)
- `test_rag_queries.py` - Old RAG test (use test_integration.py instead)
- `test_enhanced_errors.py` - Old error reporting test (now integrated)
- Various other experimental scripts

**Note:** Do not rely on deprecated tests for validation.

## Writing New Tests

### Adding Unit Tests
Place unit tests in `tests/unit/` directory:
```python
# tests/unit/test_my_service.py
import pytest
from app.services.my_service import MyService

def test_my_function():
    result = MyService.my_function()
    assert result == expected_value
```

### Adding API Tests
Place API tests in `tests/api/` directory:
```python
# tests/api/test_funds.py
import requests

def test_get_funds():
    response = requests.get("http://localhost:8000/api/funds")
    assert response.status_code == 200
```

### Adding Manual Tests
Place manual/debug scripts in `tests/manual/` directory with clear documentation.

## Continuous Integration

When setting up CI/CD, use:
```bash
# Run integration tests
python3 tests/test_integration.py

# Run unit tests
pytest tests/unit/ -v --cov=app

# Skip manual and deprecated tests
pytest tests/ -v --ignore=tests/deprecated --ignore=tests/manual
```
