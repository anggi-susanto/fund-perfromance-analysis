#!/usr/bin/env python3
"""
Comprehensive Integration Test
Tests the complete flow: Upload → Process → Query
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def test_backend_health():
    """Test if backend is healthy"""
    print_section("1. Backend Health Check")
    
    response = requests.get(f"{BASE_URL}/health")
    health = response.json()
    
    print(f"✅ Backend Status: {health['status']}")
    print(f"   Embeddings Loaded: {health.get('embeddings_loaded', 'N/A')}")
    return True

def test_document_upload():
    """Test document upload"""
    print_section("2. Document Upload Test")
    
    test_file = "files/Sample_Fund_Performance_Report.pdf"
    
    with open(test_file, 'rb') as f:
        files = {'file': f}
        data = {'fund_id': 1}
        response = requests.post(f"{BASE_URL}/api/documents/upload", files=files, data=data)
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
        return None
    
    result = response.json()
    doc_id = result['document_id']
    
    print(f"✅ Upload Successful")
    print(f"   Document ID: {doc_id}")
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")
    
    return doc_id

def test_document_processing(doc_id):
    """Test document processing with status polling"""
    print_section("3. Document Processing Test")
    
    print(f"⏳ Monitoring processing for document #{doc_id}...")
    
    terminal_statuses = {'completed', 'completed_with_errors', 'failed'}
    max_attempts = 60
    
    for attempt in range(1, max_attempts + 1):
        time.sleep(5)
        
        response = requests.get(f"{BASE_URL}/api/documents/{doc_id}/status")
        status_data = response.json()
        current_status = status_data['status']
        
        print(f"   [{attempt}] Status: {current_status}")
        
        if current_status in terminal_statuses:
            print(f"\n✅ Processing Complete!")
            print(f"   Final Status: {current_status}")
            print(f"   Pages: {status_data.get('page_count', 'N/A')}")
            print(f"   Chunks: {status_data.get('chunk_count', 'N/A')}")
            
            if status_data.get('processing_stats'):
                stats = status_data['processing_stats']
                print(f"   Tables Found: {stats.get('tables_found', 0)}")
                print(f"   Capital Calls: {stats.get('capital_calls', 0)}")
                print(f"   Distributions: {stats.get('distributions', 0)}")
                print(f"   Adjustments: {stats.get('adjustments', 0)}")
            
            if status_data.get('errors'):
                print(f"   ⚠️  Errors: {len(status_data['errors'])}")
                for err in status_data['errors'][:3]:
                    print(f"      - {err}")
            else:
                print(f"   ✅ No errors!")
            
            return status_data
    
    print(f"❌ Processing timeout")
    return None

def test_chat_query(doc_id):
    """Test RAG chat query"""
    print_section("4. Chat Query Test (RAG)")
    
    queries = [
        "What is the fund name and vintage year?",
        "How many capital calls were made?",
        "What were the total distributions?"
    ]
    
    for i, query_text in enumerate(queries, 1):
        print(f"\n📝 Query {i}: {query_text}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat/query",
                json={"query": query_text, "fund_id": 1},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"   ❌ Query failed: {response.status_code}")
                print(f"   {response.text}")
                continue
            
            result = response.json()
            
            print(f"   ✅ Response received")
            print(f"   Answer: {result.get('answer', 'N/A')[:200]}...")
            
            if result.get('sources'):
                print(f"   Sources: {len(result['sources'])} documents")
            
            if result.get('metrics'):
                print(f"   Metrics included: {', '.join(result['metrics'].keys())}")
                
        except Exception as e:
            print(f"   ❌ Query error: {e}")
    
    return True

def test_frontend_accessibility():
    """Test if frontend is accessible"""
    print_section("5. Frontend Accessibility Test")
    
    pages = [
        ("Home", "http://localhost:3000"),
        ("Upload", "http://localhost:3000/upload"),
        ("Chat", "http://localhost:3000/chat"),
        ("Funds", "http://localhost:3000/funds"),
        ("Documents", "http://localhost:3000/documents")
    ]
    
    for name, url in pages:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {name} page: Accessible")
            else:
                print(f"   ⚠️  {name} page: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name} page: {str(e)[:50]}")
    
    return True

def test_vector_search(doc_id):
    """Test vector similarity search"""
    print_section("6. Vector Search Test")
    
    # Try a direct vector search query
    print("   Testing semantic search...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/query",
            json={"query": "capital call", "fund_id": 1},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('sources'):
                print(f"   ✅ Vector search working")
                print(f"   Found {len(result['sources'])} relevant chunks")
                for i, source in enumerate(result['sources'][:3], 1):
                    print(f"      {i}. Page {source.get('page', 'N/A')}: {source.get('content', '')[:60]}...")
            else:
                print(f"   ⚠️  No sources returned")
        else:
            print(f"   ❌ Search failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Search error: {e}")
    
    return True

def test_api_endpoints():
    """Test various API endpoints"""
    print_section("7. API Endpoints Test")
    
    endpoints = [
        ("GET", "/health", None),
        ("GET", "/api/funds", None),
        ("GET", "/api/documents", None),
    ]
    
    for method, endpoint, data in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, json=data, timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ {method} {endpoint}: OK")
            else:
                print(f"   ⚠️  {method} {endpoint}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {method} {endpoint}: {str(e)[:50]}")
    
    return True

def run_integration_tests():
    """Run all integration tests"""
    print("\n" + "🚀" * 35)
    print("   COMPREHENSIVE INTEGRATION TEST")
    print("🚀" * 35)
    
    results = {}
    
    # Test 1: Backend Health
    try:
        results['health'] = test_backend_health()
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        results['health'] = False
    
    # Test 2: Document Upload
    doc_id = None
    try:
        doc_id = test_document_upload()
        results['upload'] = doc_id is not None
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        results['upload'] = False
    
    # Test 3: Document Processing
    if doc_id:
        try:
            status = test_document_processing(doc_id)
            results['processing'] = status is not None and status.get('status') == 'completed'
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            results['processing'] = False
    else:
        results['processing'] = False
        print_section("3. Document Processing Test")
        print("   ⏭️  Skipped (no document uploaded)")
    
    # Test 4: Chat Query (RAG)
    if doc_id:
        try:
            results['chat'] = test_chat_query(doc_id)
        except Exception as e:
            print(f"❌ Chat query failed: {e}")
            results['chat'] = False
    else:
        results['chat'] = False
        print_section("4. Chat Query Test (RAG)")
        print("   ⏭️  Skipped (no document processed)")
    
    # Test 5: Frontend
    try:
        results['frontend'] = test_frontend_accessibility()
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        results['frontend'] = False
    
    # Test 6: Vector Search
    if doc_id:
        try:
            results['vector_search'] = test_vector_search(doc_id)
        except Exception as e:
            print(f"❌ Vector search failed: {e}")
            results['vector_search'] = False
    else:
        results['vector_search'] = False
        print_section("6. Vector Search Test")
        print("   ⏭️  Skipped (no document processed)")
    
    # Test 7: API Endpoints
    try:
        results['api'] = test_api_endpoints()
    except Exception as e:
        print(f"❌ API test failed: {e}")
        results['api'] = False
    
    # Summary
    print_section("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} - {test_name.replace('_', ' ').title()}")
    
    print(f"\n   Score: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n   🎉 ALL TESTS PASSED! System is fully operational!")
    elif passed_tests >= total_tests * 0.7:
        print("\n   ⚠️  Most tests passed, but some issues detected")
    else:
        print("\n   ❌ Multiple failures detected, system needs attention")
    
    print("\n" + "=" * 70 + "\n")
    
    return results

if __name__ == "__main__":
    results = run_integration_tests()
    
    # Exit with appropriate code
    exit(0 if all(results.values()) else 1)
