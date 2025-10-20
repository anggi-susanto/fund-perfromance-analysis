#!/usr/bin/env python3
"""
View detailed document information including what was extracted
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def view_document_details(doc_id):
    """View all details for a document"""
    
    print("=" * 70)
    print(f"Document #{doc_id} - Detailed Analysis")
    print("=" * 70)
    
    # Get full document details
    doc_response = requests.get(f"{BASE_URL}/api/documents/{doc_id}")
    doc = doc_response.json()
    
    print("\n📄 DOCUMENT INFO")
    print("-" * 70)
    print(f"File: {doc['file_name']}")
    print(f"Fund ID: {doc['fund_id']}")
    print(f"Upload Date: {doc['upload_date']}")
    print(f"Status: {doc['parsing_status']}")
    
    if doc.get('page_count'):
        print(f"Pages: {doc['page_count']}")
    if doc.get('chunk_count'):
        print(f"Text Chunks: {doc['chunk_count']}")
    
    # Processing statistics
    if doc.get('processing_stats'):
        stats = doc['processing_stats']
        print("\n📊 PROCESSING STATISTICS")
        print("-" * 70)
        print(f"Tables Found: {stats.get('tables_found', 0)}")
        print(f"Capital Calls Extracted: {stats.get('capital_calls', 0)}")
        print(f"Distributions Extracted: {stats.get('distributions', 0)}")
        print(f"Adjustments Extracted: {stats.get('adjustments', 0)}")
        print(f"Text Chunks Created: {stats.get('text_chunks', 0)}")
        
        # Errors
        if stats.get('errors'):
            print(f"\n⚠️  ERRORS ({len(stats['errors'])})")
            print("-" * 70)
            for i, error in enumerate(stats['errors'], 1):
                print(f"{i}. {error}")
    
    # Get transactions for this fund
    fund_id = doc['fund_id']
    
    # Capital Calls
    print("\n💰 CAPITAL CALLS")
    print("-" * 70)
    cc_response = requests.get(f"{BASE_URL}/api/funds/{fund_id}/transactions/capital-calls")
    if cc_response.status_code == 200:
        capital_calls = cc_response.json()
        if capital_calls:
            for cc in capital_calls[:5]:  # Show first 5
                print(f"  {cc['call_date']}: ${cc['amount']:,.2f} - {cc.get('description', 'N/A')}")
        else:
            print("  No capital calls found")
    
    # Distributions
    print("\n📤 DISTRIBUTIONS")
    print("-" * 70)
    dist_response = requests.get(f"{BASE_URL}/api/funds/{fund_id}/transactions/distributions")
    if dist_response.status_code == 200:
        distributions = dist_response.json()
        if distributions:
            for dist in distributions[:5]:  # Show first 5
                print(f"  {dist['distribution_date']}: ${dist['amount']:,.2f} - {dist.get('description', 'N/A')}")
        else:
            print("  No distributions found")
    
    # Adjustments  
    print("\n🔧 ADJUSTMENTS")
    print("-" * 70)
    adj_response = requests.get(f"{BASE_URL}/api/funds/{fund_id}/transactions/adjustments")
    if adj_response.status_code == 200:
        adjustments = adj_response.json()
        if adjustments:
            for adj in adjustments[:5]:  # Show first 5
                print(f"  {adj['adjustment_date']}: ${adj['amount']:,.2f} - {adj.get('description', 'N/A')}")
        else:
            print("  No adjustments found")
    
    print("\n" + "=" * 70)
    print("✅ Analysis complete")
    print("=" * 70)

if __name__ == "__main__":
    import sys
    doc_id = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    view_document_details(doc_id)
