#!/usr/bin/env python3
"""
Manual test for chat interface
Tests the complete chat functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_chat_interface():
    """Test chat with fund selection"""
    print("\n" + "="*70)
    print("Testing Chat Interface with Fund Selection")
    print("="*70)
    
    # Get funds
    print("\n1️⃣  Getting available funds...")
    response = requests.get(f"{BASE_URL}/api/funds/")
    funds = response.json()
    print(f"✅ Found {len(funds)} funds")
    if funds:
        fund = funds[0]
        print(f"   Using fund: {fund['name']} (ID: {fund['id']})")
        fund_id = fund['id']
    else:
        print("❌ No funds available")
        return
    
    # Create conversation
    print("\n2️⃣  Creating conversation...")
    response = requests.post(
        f"{BASE_URL}/api/chat/conversations",
        json={"fund_id": fund_id}
    )
    conversation = response.json()
    conversation_id = conversation['conversation_id']
    print(f"✅ Conversation created: {conversation_id[:8]}...")
    
    # Test queries
    queries = [
        "What is the fund name and vintage year?",
        "Calculate the current DPI for this fund",
        "What were the total distributions?",
        "What is IRR?"
    ]
    
    print("\n3️⃣  Testing chat queries...")
    for i, query in enumerate(queries, 1):
        print(f"\n   Query {i}: {query}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat/query",
                json={
                    "query": query,
                    "fund_id": fund_id,
                    "conversation_id": conversation_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Response received ({result.get('processing_time', 0):.2f}s)")
                print(f"      Answer: {result['answer'][:100]}...")
                
                if result.get('metrics'):
                    print(f"      Metrics: {list(result['metrics'].keys())[:5]}")
                
                if result.get('sources'):
                    print(f"      Sources: {len(result['sources'])} documents")
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"      {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    # Get conversation history
    print("\n4️⃣  Retrieving conversation history...")
    response = requests.get(f"{BASE_URL}/api/chat/conversations/{conversation_id}")
    if response.status_code == 200:
        conv = response.json()
        print(f"✅ Conversation has {len(conv['messages'])} messages")
    else:
        print(f"❌ Failed to get conversation: {response.status_code}")
    
    print("\n" + "="*70)
    print("✅ Chat interface test completed!")
    print("="*70)

if __name__ == "__main__":
    test_chat_interface()
