# Architecture Redesign: Fixing the Freeze Issue

## Problem Analysis

### Current Issues
1. **Database Session Leaks**: Every request creates new `SessionLocal()` instances that are never closed
2. **Thread Pool Deadlocks**: Multiple thread pools with fixed workers cause deadlocks under load
3. **Resource Exhaustion**: Connection pool exhausted after a few requests
4. **No Cleanup**: No proper resource cleanup or lifecycle management

### Why It Freezes
```
Request 1 → Creates VectorStore → Opens DB session → Never closes
Request 2 → Creates VectorStore → Opens DB session → Never closes
Request 3 → Creates VectorStore → Opens DB session → Never closes
...
Request N → Connection pool exhausted → FREEZE (waiting for available connection)
```

## Solution: Proper Resource Management

### Key Principles
1. **Dependency Injection**: DB sessions managed by FastAPI, auto-closed after request
2. **Singleton Pattern**: LLM and embedding models initialized once, reused
3. **Default Executor**: Use asyncio's built-in thread pool instead of custom pools
4. **No Session Creation in Services**: Services receive sessions from caller

### Architecture Changes

#### Before (Problematic)
```python
class VectorStore:
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()  # ❌ Creates new session
        
class QueryEngine:
    def __init__(self, db: Session):
        self.vector_store = VectorStore()  # ❌ No db passed
        self.llm = self._initialize_llm()  # ❌ Creates new LLM each time
```

#### After (Fixed)
```python
# Singleton LLM (created once)
@lru_cache(maxsize=1)
def get_llm():
    return ChatGroq(...)  # ✅ Cached

# Singleton embeddings (created once)
@lru_cache(maxsize=1)
def get_embeddings_model():
    return HuggingFaceEmbeddings(...)  # ✅ Cached

class VectorStore:
    def __init__(self, db: Session):
        if db is None:
            raise ValueError("DB required")  # ✅ Enforces injection
        self.db = db  # ✅ Uses provided session
        self.embeddings = get_embeddings_model()  # ✅ Reuses cached model
        
class QueryEngine:
    def __init__(self, db: Session):
        self.db = db  # ✅ Uses provided session
        self.vector_store = VectorStore(db)  # ✅ Passes session
        self.llm = get_llm()  # ✅ Reuses cached LLM
```

### FastAPI Integration
```python
# Endpoint properly manages session lifecycle
@router.post("/query")
async def process_chat_query(
    request: ChatQueryRequest,
    db: Session = Depends(get_db)  # ✅ Session auto-managed
):
    query_engine = QueryEngine(db)  # ✅ Session passed in
    response = await query_engine.process_query(...)
    # ✅ Session auto-closed by FastAPI after response
    return response
```

## Migration Plan

### Step 1: Backup Current Code
```bash
cp backend/app/services/vector_store.py backend/app/services/vector_store_old.py
cp backend/app/services/query_engine.py backend/app/services/query_engine_old.py
```

### Step 2: Replace with V2 Files
```bash
mv backend/app/services/vector_store_v2.py backend/app/services/vector_store.py
mv backend/app/services/query_engine_v2.py backend/app/services/query_engine.py
```

### Step 3: Update Imports in document_processor.py
Change from:
```python
from app.services.vector_store import VectorStore

# In method
vector_store = VectorStore()  # ❌ Old way
```

To:
```python
from app.services.vector_store import VectorStore

# In method (db passed from caller)
def process_document(self, ..., db: Session):
    vector_store = VectorStore(db)  # ✅ New way
```

### Step 4: Update documents.py endpoint
```python
@router.post("/upload")
async def upload_document(
    ...,
    db: Session = Depends(get_db)  # ✅ Add db dependency
):
    processor = DocumentProcessor()
    await processor.process_document(..., db=db)  # ✅ Pass db
```

### Step 5: Test
```bash
docker compose down
docker compose up -d --build backend
python3 files/test_single_query.py
python3 files/test_concurrent_requests.py
```

## Expected Improvements

### Before
- ❌ Freezes after 3-5 requests
- ❌ Requires docker restart
- ❌ Connection pool exhausted
- ❌ Memory leaks

### After
- ✅ Handles unlimited requests
- ✅ No freezing
- ✅ Proper connection cleanup
- ✅ Stable memory usage
- ✅ Truly concurrent requests

## Key Benefits

1. **No More Freezes**: Sessions properly closed, no pool exhaustion
2. **Better Performance**: Models cached, no repeated initialization
3. **Simpler Code**: No custom thread pools, uses asyncio default
4. **Production Ready**: Proper resource management
5. **Easier Testing**: Clear dependency injection

## Testing Strategy

### 1. Single Request Test
```bash
python3 files/test_single_query.py
```
Expected: ✅ Works in 5-10s, no errors

### 2. Sequential Requests
```bash
python3 files/test_rag_with_warmup.py
```
Expected: ✅ All 3 queries succeed, no timeouts

### 3. Concurrent Requests
```bash
python3 files/test_concurrent_requests.py
```
Expected: ✅ All complete in ~25s

### 4. Stress Test
```bash
# Run 10 concurrent requests
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/chat/query \
    -H "Content-Type: application/json" \
    -d '{"query":"What is DPI?","fund_id":1}' &
done
wait
```
Expected: ✅ All succeed, no freeze

### 5. Long-Running Test
```bash
# Run 100 requests sequentially
for i in {1..100}; do
  echo "Request $i"
  curl -s -X POST http://localhost:8000/api/chat/query \
    -H "Content-Type: application/json" \
    -d '{"query":"What is DPI?","fund_id":1}' > /dev/null
done
```
Expected: ✅ No slowdown, no freeze, stable performance

## Rollback Plan

If issues occur:
```bash
# Restore old files
cp backend/app/services/vector_store_old.py backend/app/services/vector_store.py
cp backend/app/services/query_engine_old.py backend/app/services/query_engine.py
docker compose restart backend
```

## Next Steps After Fix

Once backend is stable:
1. ✅ Update todo: Mark "Fix Backend Stability" as complete
2. ✅ Proceed to Frontend Integration
3. ✅ Build upload page UI
4. ✅ Build chat interface
5. ✅ Build dashboard

The frontend can't be properly tested until the backend is rock-solid!
