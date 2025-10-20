"""
Test script to verify LLM and embeddings setup
Run with: docker compose exec backend python test_llm_setup.py
"""
import sys
sys.path.insert(0, '/app')

import asyncio
from app.core.config import settings
from app.services.vector_store import VectorStore
from app.services.query_engine import QueryEngine
from app.db.session import SessionLocal

print("\n" + "="*60)
print("LLM & EMBEDDINGS SETUP TEST")
print("="*60)

# Test 1: Check LLM Provider Configuration
print("\n[1/4] Checking LLM Configuration...")
llm_provider = getattr(settings, 'LLM_PROVIDER', 'not set')
print(f"✓ LLM Provider: {llm_provider}")

if llm_provider == 'groq':
    groq_key = getattr(settings, 'GROQ_API_KEY', '')
    if groq_key and groq_key != "your-groq-api-key-here":
        print(f"✓ Groq API Key configured: {groq_key[:15]}...{groq_key[-10:]}")
        print(f"✓ Groq Model: {settings.GROQ_MODEL}")
    else:
        print("✗ Groq API Key not configured!")
        print("  Please add GROQ_API_KEY to .env file")
        print("  Sign up at: https://console.groq.com")
        sys.exit(1)
elif llm_provider == 'openai':
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-actual-api-key-here":
        print(f"✓ OpenAI API Key configured: {settings.OPENAI_API_KEY[:20]}...{settings.OPENAI_API_KEY[-10:]}")
        print(f"✓ Model: {settings.OPENAI_MODEL}")
    else:
        print("✗ OpenAI API Key not configured!")
        sys.exit(1)
else:
    print(f"⚠️  Warning: Using {llm_provider} provider")

# Test 2: Initialize Vector Store
print("\n[2/4] Initializing Vector Store...")
try:
    vector_store = VectorStore()
    print("✓ Vector store initialized")
    print(f"✓ Using embedding model: {type(vector_store.embeddings).__name__}")
except Exception as e:
    print(f"✗ Error initializing vector store: {e}")
    sys.exit(1)

# Test 3: Test Embedding Generation
print("\n[3/4] Testing embedding generation...")
async def test_embeddings():
    try:
        test_text = "What is DPI in private equity?"
        embedding = await vector_store._get_embedding(test_text)
        print(f"✓ Generated embedding with dimension: {len(embedding)}")
        print(f"✓ Sample values: [{embedding[0]:.4f}, {embedding[1]:.4f}, ...]")
        return True
    except Exception as e:
        print(f"✗ Error generating embedding: {e}")
        return False

# Test 4: Test Query Engine
print("\n[4/4] Testing Query Engine...")
async def test_query_engine():
    try:
        db = SessionLocal()
        query_engine = QueryEngine(db)
        print(f"✓ Query engine initialized")
        print(f"✓ LLM type: {type(query_engine.llm).__name__}")
        
        # Test a simple query (without actual fund data)
        print("\n  Testing simple query classification...")
        intent = await query_engine._classify_intent("What is DPI?")
        print(f"  ✓ Intent classification: '{intent}' (expected: 'definition')")
        
        intent2 = await query_engine._classify_intent("Calculate the current DPI")
        print(f"  ✓ Intent classification: '{intent2}' (expected: 'calculation')")
        
        db.close()
        return True
    except Exception as e:
        print(f"✗ Error testing query engine: {e}")
        return False

# Run async tests
async def main():
    print("\nRunning async tests...")
    
    embedding_result = await test_embeddings()
    if not embedding_result:
        return False
    
    query_result = await test_query_engine()
    if not query_result:
        return False
    
    return True

try:
    result = asyncio.run(main())
    
    if result:
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        print("\nYour LLM setup is ready! Next steps:")
        print("  1. Generate sample PDF: cd files && python create_sample_pdf.py")
        print("  2. Upload document: POST /api/documents/upload")
        print("  3. Test chat: POST /api/chat/query")
        print("\n")
    else:
        print("\n" + "="*60)
        print("✗ SOME TESTS FAILED")
        print("="*60)
        print("\nPlease check the errors above and fix the configuration.")
        sys.exit(1)
        
except Exception as e:
    print(f"\n✗ Fatal error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
