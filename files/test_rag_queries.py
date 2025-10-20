"""
Test script for RAG query system

Tests different types of queries:
1. Definition queries (What is DPI?)
2. Calculation queries (Calculate current DPI)
3. Retrieval queries (Show capital calls)
"""
import requests
import json

# API Base URL
BASE_URL = "http://localhost:8000/api"

def test_query(query: str, fund_id: int = 9):
    """Test a query and print the response"""
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    print("⏳ Sending request to backend...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/query",
            json={
                "query": query,
                "fund_id": fund_id
            },
            timeout=30  # 30 second timeout
        )
    except requests.exceptions.Timeout:
        print("✗ Error: Request timed out after 30 seconds")
        return
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")
        return
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse:")
        print(f"  Answer: {result.get('answer', 'No answer')}")
        
        if result.get('sources'):
            print(f"\n  Sources ({len(result['sources'])} documents):")
            for i, source in enumerate(result['sources'][:2], 1):
                content = source.get('content', '')[:100]
                print(f"    {i}. {content}...")
        
        if result.get('metrics'):
            print(f"\n  Metrics:")
            for key, value in result['metrics'].items():
                if value is not None:
                    if key == 'irr' and isinstance(value, (int, float)):
                        print(f"    {key}: {value:.2%}")
                    elif isinstance(value, (int, float)):
                        if value > 1000:
                            print(f"    {key}: ${value:,.2f}")
                        else:
                            print(f"    {key}: {value:.4f}")
                    else:
                        print(f"    {key}: {value}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(f"  Response: {response.text}")


def main():
    print("="*60)
    print("RAG QUERY SYSTEM TEST")
    print("="*60)
    print("\nTesting with Fund ID 9 (latest uploaded document)")
    
    # Test 1: Definition query
    test_query("What is DPI in private equity?")
    
    # Test 2: Calculation query
    test_query("Calculate the current DPI for this fund")
    
    # Test 3: Capital calls query
    test_query("Show me the capital calls for this fund")
    
    # Test 4: Distributions query
    test_query("What distributions have been made?")
    
    # Test 5: Fund performance query
    test_query("How is the fund performing? Give me key metrics.")
    
    # Test 6: Specific date query
    test_query("What happened in 2024?")
    
    print("\n" + "="*60)
    print("TEST COMPLETED")
    print("="*60)
    print("\nNote: Query responses depend on:")
    print("  - Vector similarity search finding relevant context")
    print("  - Groq LLM generating accurate responses")
    print("  - Metrics calculator providing correct calculations")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Cannot connect to backend API")
        print("  Make sure backend is running: docker compose ps")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
