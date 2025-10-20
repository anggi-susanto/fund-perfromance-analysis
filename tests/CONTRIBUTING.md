# Contributing Tests

Guidelines for creating new tests in this project.

## Test Organization Principles

All tests must be placed in the appropriate directory based on their type:

```
tests/
├── test_integration.py       # Integration tests (full system)
├── unit/                     # Unit tests (isolated components)
├── api/                      # API endpoint tests
├── manual/                   # Manual testing scripts
└── deprecated/               # Old tests (reference only)
```

## Where to Put New Tests

### Integration Tests
**Location:** `tests/test_integration.py` (add to existing file)  
**When:** Testing complete workflows (upload → process → query)  
**Pattern:** Add new test function to existing suite

```python
def test_new_workflow():
    """Test description"""
    print_section("N. New Workflow Test")
    # Your test code
    return True
```

### Unit Tests
**Location:** `tests/unit/test_[component_name].py`  
**When:** Testing individual functions, classes, or services  
**Examples:**
- `tests/unit/test_document_processor.py`
- `tests/unit/test_vector_store.py`
- `tests/unit/test_query_engine.py`
- `tests/unit/test_metrics_calculator.py`

**Template:**
```python
"""
Unit tests for [Component Name]
"""
import pytest
from app.services.my_service import MyService

def test_function_name():
    """Test what the function does"""
    # Arrange
    input_data = "test"
    
    # Act
    result = MyService.function(input_data)
    
    # Assert
    assert result == expected_value

def test_edge_case():
    """Test edge case scenario"""
    with pytest.raises(ValueError):
        MyService.function(invalid_input)
```

### API Tests
**Location:** `tests/api/test_[endpoint_name].py`  
**When:** Testing REST API endpoints  
**Examples:**
- `tests/api/test_documents_endpoint.py`
- `tests/api/test_funds_endpoint.py`
- `tests/api/test_chat_endpoint.py`

**Template:**
```python
"""
API tests for [Endpoint Name]
"""
import requests
import pytest

BASE_URL = "http://localhost:8000/api"

def test_get_endpoint():
    """Test GET request"""
    response = requests.get(f"{BASE_URL}/endpoint")
    assert response.status_code == 200
    assert "expected_field" in response.json()

def test_post_endpoint():
    """Test POST request"""
    data = {"field": "value"}
    response = requests.post(f"{BASE_URL}/endpoint", json=data)
    assert response.status_code == 201

def test_error_handling():
    """Test error response"""
    response = requests.get(f"{BASE_URL}/endpoint/999")
    assert response.status_code == 404
```

### Manual Tests
**Location:** `tests/manual/test_[feature_name].py`  
**When:** Creating debugging or manual verification scripts  
**Examples:**
- Performance testing
- Configuration verification
- Database inspection
- Load testing

**Template:**
```python
#!/usr/bin/env python3
"""
Manual test script for [Feature Name]

Usage:
    python tests/manual/test_feature.py

Purpose:
    Describe what this script tests and when to use it
"""
import sys
sys.path.insert(0, '/app')  # If running in Docker

def main():
    print("\n" + "="*60)
    print("Testing [Feature Name]")
    print("="*60)
    
    # Your test logic here
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
```

## Naming Conventions

### File Names
- **Unit tests:** `test_[component_name].py`
  - Example: `test_table_parser.py`
- **API tests:** `test_[endpoint]_endpoint.py`
  - Example: `test_documents_endpoint.py`
- **Manual tests:** `test_[feature].py`
  - Example: `test_llm_setup.py`

### Function Names
- Use descriptive names: `test_what_is_being_tested()`
- Include context: `test_parse_capital_call_table()`
- For error cases: `test_raises_error_on_invalid_input()`

### Test Descriptions
Always include a docstring explaining:
1. What is being tested
2. Expected behavior
3. Edge cases covered (if any)

```python
def test_calculate_dpi():
    """
    Test DPI calculation with standard inputs.
    
    Should return: total_distributions / paid_in_capital
    Edge case: Returns 0 when PIC is 0
    """
    pass
```

## Running Tests

### Before Creating a New Test
Always check if it fits into existing test files:
1. Can it be added to `test_integration.py`?
2. Does a related unit test file already exist?
3. Is there a similar API test to extend?

### After Creating a Test
1. **Run the test:**
   ```bash
   # Unit test
   pytest tests/unit/test_your_file.py -v
   
   # Manual test
   python tests/manual/test_your_file.py
   ```

2. **Verify it's discoverable:**
   ```bash
   pytest tests/ --collect-only | grep your_test
   ```

3. **Update documentation:**
   - Add to `tests/README.md` if it's a major test suite
   - Update this file if you create a new test category

## Test Quality Standards

### ✅ Good Test Characteristics
- **Isolated:** Doesn't depend on other tests
- **Fast:** Runs quickly (< 1 second for unit tests)
- **Reliable:** Produces same result every time
- **Clear:** Easy to understand what failed
- **Documented:** Has clear docstring

### ❌ Avoid
- Tests that depend on specific data in database
- Tests that require manual setup
- Tests with hardcoded paths
- Tests without assertions
- Tests without descriptions

## Examples

### Example 1: Adding a Unit Test
```python
# tests/unit/test_metrics_calculator.py
"""
Unit tests for MetricsCalculator service
"""
import pytest
from decimal import Decimal
from app.services.metrics_calculator import MetricsCalculator

def test_calculate_dpi_standard():
    """Test DPI calculation with standard inputs"""
    calculator = MetricsCalculator()
    
    pic = Decimal("10000000")
    distributions = Decimal("4000000")
    
    result = calculator.calculate_dpi(pic, distributions)
    
    assert result == Decimal("0.40")

def test_calculate_dpi_zero_pic():
    """Test DPI returns 0 when PIC is 0"""
    calculator = MetricsCalculator()
    
    result = calculator.calculate_dpi(Decimal("0"), Decimal("1000"))
    
    assert result == Decimal("0")
```

### Example 2: Adding an API Test
```python
# tests/api/test_metrics_endpoint.py
"""
API tests for metrics endpoints
"""
import requests
import pytest

BASE_URL = "http://localhost:8000/api"

@pytest.fixture
def fund_id():
    """Create a test fund and return its ID"""
    response = requests.post(
        f"{BASE_URL}/funds",
        json={"name": "Test Fund", "vintage_year": 2023}
    )
    return response.json()["id"]

def test_get_fund_metrics(fund_id):
    """Test retrieving fund metrics"""
    response = requests.get(f"{BASE_URL}/funds/{fund_id}/metrics")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify all required metrics are present
    assert "dpi" in data
    assert "irr" in data
    assert "pic" in data
    assert "tvpi" in data
```

### Example 3: Adding to Integration Test
```python
# tests/test_integration.py
# Add to existing file

def test_document_deletion(doc_id):
    """Test document deletion"""
    print_section("7. Document Deletion Test")
    
    # Delete document
    response = requests.delete(f"{BASE_URL}/api/documents/{doc_id}")
    assert response.status_code == 200
    
    # Verify it's gone
    response = requests.get(f"{BASE_URL}/api/documents/{doc_id}")
    assert response.status_code == 404
    
    print("✅ Document deleted successfully")
    return True

# Then update run_integration_tests() to include it
```

## pytest Configuration

When using pytest, you can use fixtures and markers:

```python
# tests/conftest.py (if needed)
import pytest

@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for API tests"""
    return "http://localhost:8000/api"

@pytest.fixture(scope="function")
def db_session():
    """Database session for tests"""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## Test Markers

Use pytest markers to categorize tests:

```python
import pytest

@pytest.mark.slow
def test_large_document_processing():
    """Test that takes a long time"""
    pass

@pytest.mark.integration
def test_full_workflow():
    """Integration test"""
    pass

# Run only fast tests
# pytest -m "not slow"
```

## Continuous Integration

When tests are added, they should work in CI:

```yaml
# Example CI configuration
- name: Run Unit Tests
  run: pytest tests/unit/ -v --cov=app
  
- name: Run API Tests
  run: pytest tests/api/ -v
  
- name: Run Integration Tests
  run: python tests/test_integration.py
```

## Questions?

If you're unsure where to put a test:
1. Check `tests/README.md` for current organization
2. Look at similar existing tests
3. Ask: "Is this testing one thing (unit) or many things (integration)?"
4. When in doubt, start with a manual test and refactor later

---

**Remember:** Well-organized tests make the codebase more maintainable and easier to understand. Thank you for following these guidelines! 🎉
