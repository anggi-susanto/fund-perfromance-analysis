"""
Test frontend upload integration with backend
"""
import requests
import time
import os

BASE_URL = "http://localhost:8000"
SAMPLE_PDF = "/Users/albertwired/project/codtest/fund-perfromance-analysis/files/Sample_Fund_Performance_Report.pdf"

print("="*80)
print("TESTING UPLOAD INTEGRATION")
print("="*80)

# Step 1: Upload the file
print("\n1. Uploading PDF...")
with open(SAMPLE_PDF, 'rb') as f:
    files = {'file': ('Sample_Fund_Performance_Report.pdf', f, 'application/pdf')}
    data = {'fund_id': 1}
    
    response = requests.post(f"{BASE_URL}/api/documents/upload", files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ Upload successful!")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        
        document_id = result['document_id']
    else:
        print(f"   ✗ Upload failed: {response.status_code}")
        print(f"   Error: {response.text}")
        exit(1)

# Step 2: Poll for processing status
print(f"\n2. Polling document status (ID: {document_id})...")
max_attempts = 60  # 5 minutes max
attempt = 0

while attempt < max_attempts:
    time.sleep(5)  # Wait 5 seconds between polls
    attempt += 1
    
    response = requests.get(f"{BASE_URL}/api/documents/{document_id}/status")
    
    if response.status_code == 200:
        status_data = response.json()
        status = status_data['status']
        
        print(f"   Attempt {attempt}: {status}")
        
        if status == 'completed':
            print(f"   ✓ Processing completed!")
            break
        elif status == 'failed':
            print(f"   ✗ Processing failed!")
            print(f"   Error: {status_data.get('error_message', 'Unknown error')}")
            exit(1)
    else:
        print(f"   ✗ Status check failed: {response.status_code}")
        break

if attempt >= max_attempts:
    print(f"   ✗ Processing timeout after {max_attempts * 5} seconds")
    exit(1)

# Step 3: Get document details
print(f"\n3. Fetching document details...")
response = requests.get(f"{BASE_URL}/api/documents/{document_id}")

if response.status_code == 200:
    doc = response.json()
    print(f"   ✓ Document details:")
    print(f"     - File: {doc['file_name']}")
    print(f"     - Fund ID: {doc['fund_id']}")
    print(f"     - Status: {doc['parsing_status']}")
    print(f"     - Uploaded: {doc['uploaded_at']}")
else:
    print(f"   ✗ Failed to get document details")

# Step 4: Verify transactions were extracted
print(f"\n4. Checking extracted transactions...")
response = requests.get(f"{BASE_URL}/api/funds/1/transactions?transaction_type=capital_call&limit=10")

if response.status_code == 200:
    transactions = response.json()
    print(f"   ✓ Found {len(transactions)} capital calls")
    if transactions:
        print(f"     Example: {transactions[0]}")
else:
    print(f"   ✗ Failed to get transactions")

# Step 5: Test chat with uploaded document
print(f"\n5. Testing chat query...")
response = requests.post(
    f"{BASE_URL}/api/chat/query",
    json={"query": "What is DPI?", "fund_id": 1},
    timeout=30
)

if response.status_code == 200:
    chat_result = response.json()
    print(f"   ✓ Chat query successful!")
    print(f"     Answer: {chat_result.get('answer', 'N/A')[:100]}...")
    print(f"     Time: {chat_result.get('processing_time', 0)}s")
    if chat_result.get('metrics'):
        print(f"     DPI: {chat_result['metrics'].get('dpi', 'N/A')}")
else:
    print(f"   ✗ Chat query failed: {response.status_code}")

print("\n" + "="*80)
print("UPLOAD INTEGRATION TEST COMPLETE")
print("="*80)
