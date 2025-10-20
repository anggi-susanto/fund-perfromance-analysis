# Implementation Plan: Backend Stability Fix

## Executive Summary
The backend freezes after a few requests due to **database session leaks**. This document provides a clear, step-by-step plan to fix the issue properly.

## Root Cause
```
Every request creates a new database session that is never closed
→ Connection pool (default: 5-10 connections) exhausted
→ New requests wait forever for available connection
→ FREEZE
```

## Solution Overview
1. **Use FastAPI's dependency injection** for database sessions
2. **Cache expensive resources** (LLM, embeddings) as singletons
3. **Pass sessions explicitly** instead of creating them in services
4. **Use asyncio's default executor** instead of custom thread pools

## Files To Change

### 1. vector_store.py (CRITICAL)
**Problem**: Creates `SessionLocal()` in `__init__` if no session provided
**Fix**: Require session in `__init__`, remove session creation

### 2. query_engine.py (CRITICAL)
**Problem**: Creates `VectorStore()` without passing session
**Fix**: Pass session from FastAPI to VectorStore

### 3. document_processor.py (MEDIUM)
**Problem**: Creates `VectorStore()` without session
**Fix**: Accept session parameter, pass to VectorStore

### 4. documents.py endpoint (CRITICAL)
**Problem**: Doesn't pass session to DocumentProcessor
**Fix**: Add `db: Session = Depends(get_db)`, pass to processor

### 5. Remove custom thread pools (MEDIUM)
**Problem**: Custom ThreadPoolExecutor causes deadlocks
**Fix**: Use `asyncio.get_event_loop().run_in_executor(None, ...)`

## Detailed Changes

### Change 1: vector_store.py
```python
# BEFORE
def __init__(self, db: Session = None):
    self.db = db or SessionLocal()  # ❌ SESSION LEAK

# AFTER  
def __init__(self, db: Session):
    if db is None:
        raise ValueError("Database session required")
    self.db = db  # ✅ Uses provided session
```

### Change 2: query_engine.py
```python
# BEFORE
def __init__(self, db: Session):
    self.vector_store = VectorStore()  # ❌ No session passed

# AFTER
def __init__(self, db: Session):
    self.vector_store = VectorStore(db)  # ✅ Session passed
```

### Change 3: document_processor.py
```python
# BEFORE
class DocumentProcessor:
    def __init__(self):
        self.vector_store = VectorStore()  # ❌ No session
        
    async def process_document(self, file_path, document_id, fund_id):
        db = SessionLocal()  # ❌ SESSION LEAK
        # ... process ...

# AFTER
class DocumentProcessor:
    def __init__(self):
        self.table_parser = TableParser()
        # No VectorStore in __init__
        
    async def process_document(
        self, 
        file_path: str, 
        document_id: int, 
        fund_id: int,
        db: Session  # ✅ Session from FastAPI
    ):
        vector_store = VectorStore(db)  # ✅ Create with session
        # ... process ...
        # No db.close() needed - FastAPI handles it
```

### Change 4: documents.py endpoint
```python
# BEFORE
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    fund_id: int = Form(1)
):
    processor = DocumentProcessor()
    result = await processor.process_document(file_path, doc.id, fund_id)

# AFTER
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    fund_id: int = Form(1),
    db: Session = Depends(get_db)  # ✅ Session dependency
):
    processor = DocumentProcessor()
    result = await processor.process_document(
        file_path, doc.id, fund_id, db  # ✅ Pass session
    )
```

### Change 5: Remove custom thread pools
```python
# BEFORE
from concurrent.futures import ThreadPoolExecutor
_llm_thread_pool = ThreadPoolExecutor(max_workers=4)
_thread_pool = ThreadPoolExecutor(max_workers=4)

response = await loop.run_in_executor(_llm_thread_pool, ...)

# AFTER
response = await loop.run_in_executor(None, ...)  # ✅ Use default
```

## Implementation Steps

### Step 1: Apply fixes to vector_store.py
1. Change `__init__` to require `db` parameter
2. Remove `SessionLocal()` fallback
3. Change `run_in_executor` to use `None` instead of custom pool
4. Remove thread pool globals

### Step 2: Apply fixes to query_engine.py
1. Pass `db` to `VectorStore(db)`
2. Change `run_in_executor` to use `None`
3. Remove thread pool globals
4. Use `@lru_cache` for LLM singleton

### Step 3: Apply fixes to document_processor.py
1. Remove `VectorStore()` from `__init__`
2. Add `db: Session` parameter to `process_document`
3. Create `VectorStore(db)` inside method
4. Remove any `SessionLocal()` calls
5. Remove any `db.close()` calls

### Step 4: Update documents.py endpoint
1. Add `db: Session = Depends(get_db)` parameter
2. Pass `db` to `process_document`

### Step 5: Test thoroughly
```bash
# Rebuild
docker compose down
docker compose up -d --build backend

# Test 1: Single query
python3 files/test_single_query.py

# Test 2: Sequential queries  
python3 files/test_rag_with_warmup.py

# Test 3: Concurrent queries
python3 files/test_concurrent_requests.py

# Test 4: Check no freeze after 10 requests
for i in {1..10}; do
  echo "Request $i"
  curl -s -X POST http://localhost:8000/api/chat/query \
    -H "Content-Type: application/json" \
    -d '{"query":"Test","fund_id":1}' > /dev/null
  sleep 1
done

# Test 5: Health check still works
curl http://localhost:8000/health
```

## Expected Results

### Before Fix
```
Request 1: ✓ (creates session 1, never closes)
Request 2: ✓ (creates session 2, never closes)
Request 3: ✓ (creates session 3, never closes)
Request 4: ✓ (creates session 4, never closes)
Request 5: ✓ (creates session 5, never closes)
Request 6: ✗ FREEZE (waiting for available session)
```

### After Fix
```
Request 1: ✓ (borrows session, returns it)
Request 2: ✓ (borrows session, returns it)
Request 3: ✓ (borrows session, returns it)
...
Request 100: ✓ (borrows session, returns it)
Request 1000: ✓ (borrows session, returns it)
```

## Validation Checklist

- [ ] No `SessionLocal()` calls in service classes
- [ ] All services accept `db: Session` parameter
- [ ] All FastAPI endpoints use `db: Session = Depends(get_db)`
- [ ] No custom `ThreadPoolExecutor` instances
- [ ] All `run_in_executor` calls use `None` as first argument
- [ ] LLM and embeddings cached with `@lru_cache`
- [ ] Single query works
- [ ] Sequential queries work (no timeout)
- [ ] Concurrent queries work (no timeout)
- [ ] 100 requests don't cause freeze
- [ ] Memory usage stays stable

## Risk Assessment

### Low Risk Changes
- ✅ Adding `@lru_cache` decorators (only improves performance)
- ✅ Changing `run_in_executor` to use default pool (simpler)
- ✅ Adding `db` parameter to methods (backward compatible if we keep old endpoints)

### Medium Risk Changes
- ⚠️ Changing VectorStore `__init__` signature (breaks existing code)
- ⚠️ Removing `SessionLocal()` fallback (forces explicit session management)

### Mitigation
- Keep backups of old files (`_old.py` suffix)
- Test each change incrementally
- Have rollback plan ready

## Success Criteria

1. ✅ Backend doesn't freeze after 10+ requests
2. ✅ Concurrent requests all succeed
3. ✅ Memory usage stable over time
4. ✅ No database connection pool exhaustion errors
5. ✅ Health endpoint always responds
6. ✅ All existing tests still pass

## Timeline

1. **Apply fixes**: 30-45 minutes (careful, tested changes)
2. **Testing**: 15-20 minutes (run all test scenarios)
3. **Validation**: 10 minutes (check logs, monitor)
4. **Total**: ~1 hour

## Recommendation

**PROCEED WITH FIX** before frontend integration. The frontend work will be wasted if the backend keeps freezing. This fix addresses the root cause and makes the system production-ready.

The alternative (workarounds, restarts, ignoring the issue) will cause:
- ❌ Frustrated users
- ❌ Data loss (mid-request failures)
- ❌ Impossible to demo or present
- ❌ Can't deploy to production

The fix is straightforward and low-risk with proper testing.
