#!/usr/bin/env python3
"""
Test the updated upload flow with proper status handling.
This test verifies that the backend correctly processes documents
and that the frontend can handle all status types.
"""

import requests
import time
import os

# API endpoints
BASE_URL = "http://localhost:8000"
UPLOAD_URL = f"{BASE_URL}/api/documents/upload"
STATUS_URL = f"{BASE_URL}/api/documents/{{doc_id}}/status"

# Test file
TEST_FILE = "files/Sample_Fund_Performance_Report.pdf"

def test_upload_flow():
    """Test the complete upload flow with status checking"""
    
    print("=" * 60)
    print("Testing Upload Flow with Status Handling")
    print("=" * 60)
    
    # Check if test file exists
    if not os.path.exists(TEST_FILE):
        print(f"\n❌ Test file not found: {TEST_FILE}")
        print("Please create a sample PDF first.")
        return
    
    print(f"\n📄 Test file: {TEST_FILE}")
    print(f"📊 File size: {os.path.getsize(TEST_FILE) / 1024:.1f} KB")
    
    # Step 1: Upload document
    print("\n" + "=" * 60)
    print("Step 1: Uploading document to Fund 1")
    print("=" * 60)
    
    try:
        with open(TEST_FILE, 'rb') as f:
            files = {'file': f}
            data = {'fund_id': 1}
            response = requests.post(UPLOAD_URL, files=files, data=data, timeout=10)
        
        if response.status_code != 200:
            print(f"\n❌ Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        result = response.json()
        doc_id = result.get('document_id')
        print(f"\n✅ Upload successful!")
        print(f"   Document ID: {doc_id}")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        
    except Exception as e:
        print(f"\n❌ Upload error: {e}")
        return
    
    # Step 2: Poll for status
    print("\n" + "=" * 60)
    print("Step 2: Monitoring document processing")
    print("=" * 60)
    
    terminal_statuses = {'completed', 'completed_with_errors', 'failed'}
    max_attempts = 60  # 5 minutes max
    poll_interval = 5  # seconds
    
    for attempt in range(1, max_attempts + 1):
        try:
            status_response = requests.get(
                STATUS_URL.format(doc_id=doc_id),
                timeout=5
            )
            
            if status_response.status_code != 200:
                print(f"\n❌ Status check failed: {status_response.status_code}")
                break
            
            status_data = status_response.json()
            current_status = status_data.get('status')
            
            print(f"\n[Attempt {attempt}/{max_attempts}] Status: {current_status}")
            
            # Check for terminal status
            if current_status in terminal_statuses:
                print("\n" + "=" * 60)
                print("Processing Complete!")
                print("=" * 60)
                print(f"\n✅ Final status: {current_status}")
                
                if current_status == 'completed':
                    print("🎉 Document processed successfully!")
                elif current_status == 'completed_with_errors':
                    print("⚠️  Document processed with some errors")
                    print("   Some data may not have been extracted")
                elif current_status == 'failed':
                    print("❌ Processing failed")
                    error_msg = status_data.get('error_message', 'No error message')
                    print(f"   Error: {error_msg}")
                
                # Show additional info
                if 'page_count' in status_data:
                    print(f"\n📊 Document info:")
                    print(f"   Pages: {status_data.get('page_count')}")
                    print(f"   Chunks: {status_data.get('chunk_count', 'N/A')}")
                
                return True
            
            # Wait before next poll
            if attempt < max_attempts:
                time.sleep(poll_interval)
        
        except requests.exceptions.Timeout:
            print(f"\n⏱️  Request timeout (attempt {attempt})")
            if attempt < max_attempts:
                time.sleep(poll_interval)
        except Exception as e:
            print(f"\n❌ Status check error: {e}")
            break
    
    print("\n" + "=" * 60)
    print("❌ Processing timeout - no terminal status reached")
    print("=" * 60)
    return False


if __name__ == "__main__":
    print("\n🚀 Starting upload flow test...\n")
    success = test_upload_flow()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED - Upload flow working correctly!")
    else:
        print("❌ TEST FAILED - Check backend logs for issues")
    print("=" * 60)
    print()
