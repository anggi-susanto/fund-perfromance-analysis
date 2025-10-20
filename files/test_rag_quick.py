"""
Quick RAG test - Tests just 1-2 queries to verify system is working
"""
import requests
import time

BASE_URL = "http://localhost:8000/api"

def quick_test():
    print("="*60)
    print("QUICK RAG TEST")
    print("="*60)
    
    # Test 1: Simple query with extended timeout
    print("\n[Test 1] Testing: 'What is DPI?'")
    print("⏳ This may take 10-30 seconds on first run (loading models)...")
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/chat/query",
            json={"query": "What is DPI?", "fund_id": 9},
            timeout=60  # 60 second timeout for first query
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Success! (took {elapsed:.1f}s)")
            answer = result.get('answer', '')
            if len(answer) > 200:
                print(f"  Answer: {answer[:200]}...")
            else:
                print(f"  Answer: {answer}")
            
            if result.get('metrics'):
                print(f"  Metrics: DPI={result['metrics'].get('dpi', 'N/A')}, PIC=${result['metrics'].get('pic', 0):,.0f}")
            
            print(f"  Processing time: {result.get('processing_time', 0):.2f}s")
        else:
            print(f"✗ Failed with status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"✗ Timeout after {elapsed:.1f}s")
        print("  The backend might still be loading models. Try again in a minute.")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Second query should be faster (models cached)
    print("\n[Test 2] Testing: 'Calculate DPI'")
    print("⏳ Waiting 5 seconds to ensure first query completed...")
    time.sleep(5)
    print("Now testing second query...")
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/chat/query",
            json={"query": "Calculate the current DPI", "fund_id": 9},
            timeout=60
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Success! (took {elapsed:.1f}s)")
            answer = result.get('answer', '')
            if len(answer) > 150:
                print(f"  Answer: {answer[:150]}...")
            else:
                print(f"  Answer: {answer}")
        else:
            print(f"✗ Failed with status {response.status_code}")
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"✗ Timeout after {elapsed:.1f}s")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*60)
    print("QUICK TEST COMPLETED")
    print("="*60)
    print("\nIf both tests passed, the RAG system is working!")
    print("If timeouts occurred, try:")
    print("  1. Wait 1-2 minutes for models to fully load")
    print("  2. Check backend logs: docker compose logs backend")
    print("  3. Restart backend: docker compose restart backend")

if __name__ == "__main__":
    try:
        quick_test()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
