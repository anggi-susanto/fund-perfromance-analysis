"""
Test RAG queries with warmup (accepts first-request slowness)
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_query(query: str, timeout: int = 60):
    """Test a single query"""
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/query",
            json={
                "query": query,
                "fund_id": 1
            },
            timeout=timeout
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success! (took {elapsed:.1f}s)")
            print(f"\nIntent: {data.get('intent', 'N/A')}")
            print(f"\nResponse:\n{data.get('response', 'N/A')}")
            
            if data.get('metrics'):
                print(f"\nMetrics:")
                for key, value in data['metrics'].items():
                    print(f"  {key}: {value}")
            
            return True
        else:
            print(f"✗ Error {response.status_code}: {response.text}")
            return False
            
    except requests.Timeout:
        elapsed = time.time() - start
        print(f"✗ Timeout after {elapsed:.1f}s")
        return False
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ Error after {elapsed:.1f}s: {e}")
        return False

if __name__ == "__main__":
    print("Testing RAG queries with warmup...")
    print("Note: First query may take 10-30s to load embedding model")
    
    queries = [
        "What is DPI?",  # Should take 10-30s (warmup)
        "Calculate DPI for the fund",  # Should be fast (cached)
        "What capital calls were made?"  # Should be fast (cached)
    ]
    
    results = []
    for i, query in enumerate(queries, 1):
        if i == 1:
            print(f"\nTest {i}/3 (WARMUP - may take 10-30s):")
            # First query gets 120s timeout for model loading
            success = test_query(query, timeout=120)
        else:
            print(f"\nTest {i}/3 (should be fast):")
            # Subsequent queries should be fast with caching
            success = test_query(query, timeout=30)
        
        results.append(success)
        
        # Small delay between queries
        if i < len(queries):
            time.sleep(2)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
