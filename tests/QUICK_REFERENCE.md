# Test Quick Reference

Quick reference for creating tests in this project.

## 📍 Where to Put Tests

| Test Type | Location | Example |
|-----------|----------|---------|
| **Integration** | `tests/test_integration.py` | Add to existing file |
| **Unit** | `tests/unit/test_[component].py` | `test_vector_store.py` |
| **API** | `tests/api/test_[endpoint].py` | `test_documents_endpoint.py` |
| **Manual** | `tests/manual/test_[feature].py` | `test_llm_setup.py` |

## 🎯 Decision Tree

```
Is it testing the complete system flow?
├── YES → Add to tests/test_integration.py
└── NO → Is it testing a single function/class?
    ├── YES → Create tests/unit/test_[component].py
    └── NO → Is it testing an API endpoint?
        ├── YES → Create tests/api/test_[endpoint].py
        └── NO → Is it for manual debugging?
            ├── YES → Create tests/manual/test_[feature].py
            └── NO → Ask for guidance
```

## 📝 Quick Templates

### Unit Test
```python
# tests/unit/test_my_component.py
"""Unit tests for MyComponent"""
import pytest
from app.services.my_component import MyComponent

def test_function_name():
    """Test description"""
    result = MyComponent.function()
    assert result == expected
```

### API Test
```python
# tests/api/test_my_endpoint.py
"""API tests for /my/endpoint"""
import requests

BASE_URL = "http://localhost:8000/api"

def test_get_endpoint():
    """Test GET request"""
    response = requests.get(f"{BASE_URL}/my/endpoint")
    assert response.status_code == 200
```

### Manual Test
```python
# tests/manual/test_my_feature.py
#!/usr/bin/env python3
"""Manual test for my feature"""

def main():
    print("Testing my feature...")
    # Your test code
    print("✅ Done!")

if __name__ == "__main__":
    main()
```

## ▶️ Running Tests

```bash
# All integration tests (recommended)
python3 tests/test_integration.py

# Specific unit test
pytest tests/unit/test_component.py -v

# All unit tests
pytest tests/unit/ -v

# All API tests
pytest tests/api/ -v

# Manual test
python3 tests/manual/test_feature.py
```

## ✅ Checklist Before Committing

- [ ] Test file is in the correct directory
- [ ] File name follows convention: `test_*.py`
- [ ] Test functions start with `test_`
- [ ] All tests have docstrings
- [ ] Tests are isolated (don't depend on each other)
- [ ] Tests pass: `pytest path/to/test.py -v`
- [ ] Updated `tests/README.md` if adding new test suite

## 📚 More Info

- **Detailed guidelines:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **Test documentation:** [README.md](README.md)
- **Project structure:** [../README.md](../README.md)

---

**Need help?** Check existing tests for examples or ask for guidance.
