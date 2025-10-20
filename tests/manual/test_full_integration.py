#!/usr/bin/env python3
"""
Full Integration Test for Fund Performance Analysis System

This test verifies all frontend-backend interactions:
1. Upload Page - Document upload and processing
2. Documents Page - Document listing and filtering
3. Funds Page - Portfolio overview and fund details
4. Chat Page - Natural language queries with fund context

Run this test to validate the entire system end-to-end.
"""

import requests
import time
import sys
from pathlib import Path
from datetime import datetime

# API Configuration
API_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

# Test Results Tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}

def log_test(test_name, passed, details=""):
    """Log test result"""
    test_results["total"] += 1
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status}: {test_name}")
    if details:
        print(f"  Details: {details}")
    
    if passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
        test_results["errors"].append(f"{test_name}: {details}")

def print_header(section_name):
    """Print section header"""
    print(f"\n{'=' * 80}")
    print(f"  {section_name}")
    print(f"{'=' * 80}")

def check_service_health():
    """Check if backend services are running"""
    print_header("SERVICE HEALTH CHECK")
    
    try:
        # Check backend
        response = requests.get(f"{API_URL}/docs", timeout=5)
        log_test("Backend Service Running", response.status_code == 200, 
                f"Status: {response.status_code}")
        
        # Check database connection
        response = requests.get(f"{API_URL}/api/funds/", timeout=5)
        log_test("Database Connection", response.status_code == 200,
                f"Status: {response.status_code}")
        
        return True
    except Exception as e:
        log_test("Service Health", False, str(e))
        return False

def test_fund_api():
    """Test fund-related API endpoints"""
    print_header("FUND API TESTS")
    
    try:
        # List all funds
        response = requests.get(f"{API_URL}/api/funds/")
        log_test("List Funds API", response.status_code == 200,
                f"Found {len(response.json())} funds")
        
        funds = response.json()
        if not funds:
            log_test("Funds Exist", False, "No funds found in database")
            return None
        
        # Get first fund details
        fund_id = funds[0]['id']
        fund_name = funds[0]['name']
        response = requests.get(f"{API_URL}/api/funds/{fund_id}")
        log_test("Get Fund Details API", response.status_code == 200,
                f"Retrieved: {fund_name}")
        
        # Get fund metrics
        response = requests.get(f"{API_URL}/api/funds/{fund_id}/metrics")
        log_test("Get Fund Metrics API", response.status_code == 200,
                f"Metrics retrieved")
        
        metrics = response.json()
        has_metrics = any([
            metrics.get('dpi'),
            metrics.get('irr'),
            metrics.get('tvpi'),
            metrics.get('pic')
        ])
        log_test("Fund Has Metrics", has_metrics,
                f"DPI: {metrics.get('dpi')}, IRR: {metrics.get('irr')}")
        
        # Get fund transactions
        for txn_type in ['capital_calls', 'distributions', 'adjustments']:
            response = requests.get(
                f"{API_URL}/api/funds/{fund_id}/transactions",
                params={"transaction_type": txn_type, "page": 1, "limit": 10}
            )
            log_test(f"Get {txn_type.replace('_', ' ').title()} API",
                    response.status_code == 200,
                    f"Count: {len(response.json().get('items', []))}")
        
        return fund_id, fund_name
        
    except Exception as e:
        log_test("Fund API", False, str(e))
        return None

def test_document_api():
    """Test document-related API endpoints"""
    print_header("DOCUMENT API TESTS")
    
    try:
        # List all documents
        response = requests.get(f"{API_URL}/api/documents/")
        log_test("List Documents API", response.status_code == 200,
                f"Found {len(response.json())} documents")
        
        documents = response.json()
        if not documents:
            log_test("Documents Exist", False, "No documents found")
            return None
        
        # Get document details
        doc_id = documents[0]['id']
        doc_name = documents[0]['file_name']
        response = requests.get(f"{API_URL}/api/documents/{doc_id}/status")
        log_test("Get Document Status API", response.status_code == 200,
                f"Document: {doc_name}")
        
        doc_status = response.json()
        log_test("Document Processing Complete",
                doc_status['status'] in ['completed', 'completed_with_errors'],
                f"Status: {doc_status['status']}")
        
        # Check processing stats
        has_stats = doc_status.get('page_count') or doc_status.get('chunk_count')
        log_test("Document Has Processing Stats", has_stats,
                f"Pages: {doc_status.get('page_count')}, Chunks: {doc_status.get('chunk_count')}")
        
        return doc_id, doc_name
        
    except Exception as e:
        log_test("Document API", False, str(e))
        return None

def test_chat_api(fund_id=None):
    """Test chat/query API endpoints"""
    print_header("CHAT API TESTS")
    
    try:
        # Create conversation
        payload = {}
        if fund_id:
            payload['fund_id'] = fund_id
        
        response = requests.post(f"{API_URL}/api/chat/conversations", json=payload)
        log_test("Create Conversation API", response.status_code == 200)
        
        conversation_id = response.json().get('conversation_id')
        
        # Test queries
        queries = [
            "What is the DPI of this fund?",
            "Show me the IRR",
            "What are the recent capital calls?"
        ]
        
        for i, query in enumerate(queries, 1):
            start_time = time.time()
            
            payload = {
                "query": query,
                "conversation_id": conversation_id
            }
            if fund_id:
                payload['fund_id'] = fund_id
            
            response = requests.post(f"{API_URL}/api/chat/query", json=payload, timeout=30)
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                log_test(f"Chat Query #{i}", True,
                        f"Response in {response_time:.2f}s, Tokens: {result.get('metrics', {}).get('total_tokens', 'N/A')}")
                
                # Check response structure
                has_answer = bool(result.get('answer'))
                log_test(f"Query #{i} Has Answer", has_answer,
                        f"Answer length: {len(result.get('answer', ''))}")
                
                # Check for metrics in response
                has_metrics = bool(result.get('metrics_data'))
                if has_metrics:
                    log_test(f"Query #{i} Includes Metrics", True,
                            f"Metrics: {list(result['metrics_data'].keys())}")
                
                # Check for sources
                has_sources = bool(result.get('sources'))
                if has_sources:
                    log_test(f"Query #{i} Has Sources", True,
                            f"Sources: {len(result['sources'])}")
            else:
                log_test(f"Chat Query #{i}", False,
                        f"Status: {response.status_code}")
        
        return conversation_id
        
    except Exception as e:
        log_test("Chat API", False, str(e))
        return None

def test_metrics_api(fund_id):
    """Test metrics calculation API"""
    print_header("METRICS API TESTS")
    
    try:
        # Get all metrics
        response = requests.get(f"{API_URL}/api/metrics/funds/{fund_id}/metrics")
        log_test("Get All Metrics API", response.status_code == 200)
        
        if response.status_code == 200:
            metrics = response.json()
            
            # Check individual metrics
            metric_types = ['dpi', 'irr', 'tvpi', 'moic']
            for metric_type in metric_types:
                if metric_type in metrics:
                    log_test(f"Metric: {metric_type.upper()}", True,
                            f"Value: {metrics[metric_type]}")
        
        # Test individual metric endpoints
        for metric in ['dpi', 'irr']:
            response = requests.get(
                f"{API_URL}/api/metrics/funds/{fund_id}/metrics",
                params={"metric": metric}
            )
            log_test(f"Get {metric.upper()} Metric API", response.status_code == 200)
        
    except Exception as e:
        log_test("Metrics API", False, str(e))

def test_page_navigation():
    """Test that frontend pages are accessible"""
    print_header("PAGE NAVIGATION TESTS")
    
    pages = [
        ("/", "Home/Landing Page"),
        ("/upload", "Upload Page"),
        ("/documents", "Documents Page"),
        ("/funds", "Funds Dashboard"),
        ("/chat", "Chat Page"),
    ]
    
    for path, name in pages:
        try:
            response = requests.get(f"{FRONTEND_URL}{path}", timeout=5)
            log_test(f"Frontend: {name}", response.status_code == 200,
                    f"Status: {response.status_code}")
        except Exception as e:
            log_test(f"Frontend: {name}", False, str(e))

def print_summary():
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ({pass_rate:.1f}%)")
    print(f"Failed: {failed}")
    
    if test_results["errors"]:
        print("\n❌ Failed Tests:")
        for error in test_results["errors"]:
            print(f"  - {error}")
    
    print(f"\n{'=' * 80}\n")
    
    return failed == 0

def main():
    """Run all integration tests"""
    print("\n" + "=" * 80)
    print("  FUND PERFORMANCE ANALYSIS - FULL INTEGRATION TEST")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 80)
    
    # Check services
    if not check_service_health():
        print("\n❌ Services not running. Start with: docker compose up")
        return False
    
    # Test APIs
    fund_result = test_fund_api()
    doc_result = test_document_api()
    
    # Test chat with fund context if available
    if fund_result:
        fund_id, fund_name = fund_result
        print(f"\n📊 Testing with fund: {fund_name} (ID: {fund_id})")
        test_chat_api(fund_id)
        test_metrics_api(fund_id)
    else:
        print("\n⚠️  Skipping fund-specific tests (no funds available)")
    
    # Test frontend pages
    test_page_navigation()
    
    # Print summary
    success = print_summary()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
