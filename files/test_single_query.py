"""
Simple single query test
"""
import requests
import time

BASE_URL = "http://localhost:8000"

print("Testing single query...")
print("Query: What is DPI?")

start = time.time()
try:
    response = requests.post(
        f"{BASE_URL}/api/chat/query",
        json={"query": "What is DPI?", "fund_id": 1},
        timeout=60
    )
    elapsed = time.time() - start
    
    print(f"\nStatus: {response.status_code}")
    print(f"Time: {elapsed:.1f}s")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nResponse: {data.get('response', 'N/A')[:200]}...")
        print(f"\nMetrics: {data.get('metrics', {})}")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    elapsed = time.time() - start
    print(f"\nError after {elapsed:.1f}s: {e}")
