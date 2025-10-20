#!/usr/bin/env python3
"""
Test upload with enhanced error reporting
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"
TEST_FILE = "files/Sample_Fund_Performance_Report.pdf"

def test_enhanced_upload():
    """Test upload and check for detailed error reporting"""
    
    print("=" * 70)
    print("Testing Enhanced Error Reporting")
    print("=" * 70)
    
    # Upload document
    print("\n📤 Uploading document...")
    with open(TEST_FILE, 'rb') as f:
        files = {'file': f}
        data = {'fund_id': 1}
        response = requests.post(f"{BASE_URL}/api/documents/upload", files=files, data=data)
    
    result = response.json()
    doc_id = result['document_id']
    print(f"✅ Document ID: {doc_id}")
    
    # Poll for completion
    print("\n⏳ Waiting for processing to complete...")
    terminal_statuses = {'completed', 'completed_with_errors', 'failed'}
    
    for attempt in range(1, 61):
        time.sleep(5)
        status_response = requests.get(f"{BASE_URL}/api/documents/{doc_id}/status")
        status_data = status_response.json()
        current_status = status_data['status']
        
        print(f"  [{attempt}] Status: {current_status}")
        
        if current_status in terminal_statuses:
            print("\n" + "=" * 70)
            print("📊 DETAILED PROCESSING REPORT")
            print("=" * 70)
            
            # Display all available information
            print(f"\n🔍 Document ID: {status_data['document_id']}")
            print(f"📋 Status: {status_data['status']}")
            
            if status_data.get('page_count'):
                print(f"📄 Pages: {status_data['page_count']}")
            
            if status_data.get('chunk_count'):
                print(f"📝 Text Chunks: {status_data['chunk_count']}")
            
            # Display processing statistics
            if status_data.get('processing_stats'):
                stats = status_data['processing_stats']
                print(f"\n📈 Processing Statistics:")
                print(f"   Tables Found: {stats.get('tables_found', 0)}")
                print(f"   Capital Calls: {stats.get('capital_calls', 0)}")
                print(f"   Distributions: {stats.get('distributions', 0)}")
                print(f"   Adjustments: {stats.get('adjustments', 0)}")
                print(f"   Text Chunks: {stats.get('text_chunks', 0)}")
            
            # Display errors if any
            if status_data.get('errors'):
                errors = status_data['errors']
                print(f"\n⚠️  Errors Encountered: {len(errors)}")
                print("-" * 70)
                for i, error in enumerate(errors, 1):
                    print(f"{i}. {error}")
                print("-" * 70)
            elif status_data.get('error_message'):
                print(f"\n❌ Error: {status_data['error_message']}")
            else:
                print("\n✅ No errors - processing completed successfully!")
            
            # Display full JSON for debugging
            print(f"\n📦 Full Response:")
            print(json.dumps(status_data, indent=2))
            
            print("\n" + "=" * 70)
            return True
    
    print("\n❌ Timeout waiting for processing")
    return False

if __name__ == "__main__":
    test_enhanced_upload()
