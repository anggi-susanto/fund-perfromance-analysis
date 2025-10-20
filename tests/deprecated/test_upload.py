"""
Test script to upload document to the backend API

This script:
1. Creates a test fund
2. Uploads the sample PDF
3. Checks processing status
"""
import requests
import time
import json

# API Base URL
BASE_URL = "http://localhost:8000/api"

def create_fund():
    """Create a test fund"""
    print("\n[1/3] Creating test fund...")
    
    fund_data = {
        "name": "Tech Ventures Fund III",
        "gp_name": "Tech Ventures Partners",
        "vintage_year": 2023,
        "fund_type": "Venture Capital"
    }
    
    response = requests.post(f"{BASE_URL}/funds/", json=fund_data)
    
    if response.status_code == 200:
        fund = response.json()
        print(f"✓ Fund created successfully!")
        print(f"  ID: {fund['id']}")
        print(f"  Name: {fund['name']}")
        print(f"  GP: {fund.get('gp_name', 'N/A')}")
        print(f"  Vintage Year: {fund.get('vintage_year', 'N/A')}")
        return fund['id']
    else:
        print(f"✗ Error creating fund: {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def upload_document(fund_id, file_path):
    """Upload document to the API"""
    print(f"\n[2/3] Uploading document...")
    
    with open(file_path, 'rb') as f:
        files = {'file': ('Sample_Fund_Performance_Report.pdf', f, 'application/pdf')}
        data = {'fund_id': fund_id}
        
        response = requests.post(f"{BASE_URL}/documents/upload", files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Document uploaded successfully!")
        print(f"  Document ID: {result['document_id']}")
        print(f"  Status: {result['status']}")
        print(f"  Message: {result['message']}")
        return result['document_id']
    else:
        print(f"✗ Error uploading document: {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def check_status(document_id):
    """Check document processing status"""
    print(f"\n[3/3] Checking processing status...")
    
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        time.sleep(2)  # Wait 2 seconds between checks
        attempt += 1
        
        response = requests.get(f"{BASE_URL}/documents/{document_id}/status")
        
        if response.status_code == 200:
            status = response.json()
            
            if status['status'] == 'processing':
                print(f"  [{attempt}/{max_attempts}] Status: Processing...")
            elif status['status'] == 'completed':
                print(f"\n✓ Document processing completed!")
                return True
            elif status['status'] == 'failed':
                print(f"\n✗ Document processing failed!")
                if status.get('error_message'):
                    print(f"  Error: {status['error_message']}")
                return False
            elif status['status'] == 'pending':
                print(f"  [{attempt}/{max_attempts}] Status: Pending...")
        else:
            print(f"✗ Error checking status: {response.status_code}")
            return False
    
    print(f"\n⚠️  Processing timeout (waited {max_attempts * 2} seconds)")
    return False


def verify_data(fund_id):
    """Verify that data was extracted correctly"""
    print(f"\n[Verification] Checking extracted data...")
    
    # Check capital calls
    response = requests.get(
        f"{BASE_URL}/funds/{fund_id}/transactions",
        params={"transaction_type": "capital_calls"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Capital Calls: {result['total']} found")
        if result['total'] > 0:
            for item in result['items'][:3]:  # Show first 3
                amount = float(item['amount'])
                print(f"  - {item['call_date']}: ${amount:,.2f}")
    
    # Check distributions
    response = requests.get(
        f"{BASE_URL}/funds/{fund_id}/transactions",
        params={"transaction_type": "distributions"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Distributions: {result['total']} found")
        if result['total'] > 0:
            for item in result['items'][:3]:  # Show first 3
                amount = float(item['amount'])
                print(f"  - {item['distribution_date']}: ${amount:,.2f}")
    
    # Check adjustments
    response = requests.get(
        f"{BASE_URL}/funds/{fund_id}/transactions",
        params={"transaction_type": "adjustments"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Adjustments: {result['total']} found")
        if result['total'] > 0:
            for item in result['items'][:3]:  # Show first 3
                amount = float(item['amount'])
                print(f"  - {item['adjustment_date']}: ${amount:,.2f}")
    
    # Check metrics
    response = requests.get(f"{BASE_URL}/funds/{fund_id}/metrics")
    
    if response.status_code == 200:
        metrics = response.json()
        print(f"\n✓ Fund Metrics:")
        print(f"  PIC: ${metrics.get('pic') or 0:,.2f}")
        print(f"  Total Distributions: ${metrics.get('total_distributions') or 0:,.2f}")
        print(f"  DPI: {metrics.get('dpi') or 0:.4f}")
        irr = metrics.get('irr')
        if irr is not None:
            print(f"  IRR: {irr:.2%}")
        else:
            print(f"  IRR: Not available")
        print(f"  TVPI: {metrics.get('tvpi') or 0:.4f}")
        print(f"  NAV: ${metrics.get('nav') or 0:,.2f}")


def main():
    print("="*60)
    print("DOCUMENT UPLOAD TEST")
    print("="*60)
    
    try:
        # Step 1: Create fund
        fund_id = create_fund()
        if not fund_id:
            return
        
        # Step 2: Upload document
        pdf_path = "Sample_Fund_Performance_Report.pdf"
        document_id = upload_document(fund_id, pdf_path)
        if not document_id:
            return
        
        # Step 3: Check processing status
        success = check_status(document_id)
        
        if success:
            # Step 4: Verify data
            verify_data(fund_id)
            
            print("\n" + "="*60)
            print("✓ TEST COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("\nNext steps:")
            print("  1. Test RAG queries via API: POST /api/chat/query")
            print("  2. Connect frontend upload page")
            print("  3. Connect frontend chat interface")
        else:
            print("\n" + "="*60)
            print("✗ TEST FAILED")
            print("="*60)
            print("\nCheck backend logs for errors:")
            print("  docker compose logs backend")
    
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Cannot connect to backend API")
        print("  Make sure backend is running: docker compose ps")
        print("  Start backend: docker compose up -d backend")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
