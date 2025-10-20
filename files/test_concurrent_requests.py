"""
Test concurrent requests to verify async is working
"""
import requests
import time
from threading import Thread
from queue import Queue

BASE_URL = "http://localhost:8000"

def make_request(query, result_queue, timeout=60):
    """Make a single request and put result in queue"""
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/query",
            json={"query": query, "fund_id": 1},
            timeout=timeout
        )
        elapsed = time.time() - start
        result_queue.put({
            "query": query,
            "success": response.status_code == 200,
            "time": elapsed,
            "status": response.status_code
        })
    except requests.Timeout:
        elapsed = time.time() - start
        result_queue.put({
            "query": query,
            "success": False,
            "time": elapsed,
            "error": "Timeout"
        })
    except Exception as e:
        elapsed = time.time() - start
        result_queue.put({
            "query": query,
            "success": False,
            "time": elapsed,
            "error": str(e)
        })

if __name__ == "__main__":
    print("Testing concurrent requests...")
    print("Sending 3 requests simultaneously")
    print("="*80)
    
    queries = [
        "What is DPI?",
        "Calculate DPI",
        "What capital calls were made?"
    ]
    
    # Start all requests concurrently
    result_queue = Queue()
    threads = []
    
    start_time = time.time()
    for query in queries:
        t = Thread(target=make_request, args=(query, result_queue, 60))
        t.start()
        threads.append(t)
        print(f"Started: {query}")
    
    # Wait for all to complete
    for t in threads:
        t.join()
    
    total_time = time.time() - start_time
    
    # Collect results
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())
    
    # Print results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    for r in results:
        status = "✓" if r["success"] else "✗"
        query_short = r["query"][:40] + "..." if len(r["query"]) > 40 else r["query"]
        print(f"{status} {query_short}: {r['time']:.1f}s", end="")
        if not r["success"]:
            error = r.get("error", f"Status {r.get('status', '?')}")
            print(f" ({error})")
        else:
            print()
    
    print(f"\nTotal time: {total_time:.1f}s")
    print(f"Success: {sum(1 for r in results if r['success'])}/{len(results)}")
    
    # Check if requests were truly concurrent
    if all(r["success"] for r in results):
        max_time = max(r["time"] for r in results)
        if total_time < max_time * 1.5:  # If total time is close to longest request
            print("\n✓ Requests appear to be handled concurrently!")
        else:
            print("\n✗ Requests seem to be queued (total time much longer than longest request)")
    else:
        print("\n✗ Some requests failed")
