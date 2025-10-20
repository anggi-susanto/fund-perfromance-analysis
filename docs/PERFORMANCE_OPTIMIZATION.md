# Performance Optimization Summary

## Issue Identified
The fund performance analysis system had a **critical blocking issue** where slow requests would block all subsequent requests, causing timeouts.

### Root Cause
1. **Synchronous embedding calls**: The `HuggingFaceEmbeddings.embed_query()` method was being called synchronously in an async function, blocking the event loop
2. **Synchronous LLM calls**: The `ChatGroq.invoke()` method was also synchronous, causing further blocking
3. **Single-worker Uvicorn**: Default configuration only handled one request at a time

## Fixes Applied

### 1. Async Embedding Calls (`vector_store.py`)
```python
# Added thread pool for blocking operations
_thread_pool = ThreadPoolExecutor(max_workers=4)

async def _get_embedding(self, text: str) -> np.ndarray:
    """Generate embedding for text (runs in thread pool to avoid blocking)"""
    loop = asyncio.get_event_loop()
    
    def _embed():
        if hasattr(self.embeddings, 'embed_query'):
            embedding = self.embeddings.embed_query(text)
        else:
            embedding = self.embeddings.encode(text)
        return np.array(embedding, dtype=np.float32)
    
    # Run the blocking embedding call in a thread pool
    return await loop.run_in_executor(_thread_pool, _embed)
```

### 2. Async LLM Calls (`query_engine.py`)
```python
# Added thread pool for LLM calls
_llm_thread_pool = ThreadPoolExecutor(max_workers=4)

async def _generate_response(...):
    ...
    # Run blocking LLM call in thread pool
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(_llm_thread_pool, self.llm.invoke, messages)
    ...
```

### 3. Global Embedding Model Cache (`vector_store.py`)
```python
# Cache embedding model across all requests
_embeddings_cache = None

def _initialize_embeddings(self):
    global _embeddings_cache
    if _embeddings_cache is not None:
        return _embeddings_cache
    
    # Load model only once
    _embeddings_cache = HuggingFaceEmbeddings(...)
    return _embeddings_cache
```

## Test Results

### Before Fixes
- **Sequential requests**: First request: ✓ (7-30s), Subsequent requests: ✗ (timeout)
- **Concurrent requests**: All requests timed out or blocked
- **Diagnosis**: Each request blocked the entire server

### After Fixes
- **Single query**: ✓ Success in 7.6s
- **Concurrent requests** (3 simultaneous): ✓ All completed in ~23s
  - Without async: Would take 60-90s sequentially
  - With async: 23s (3x faster, truly concurrent)

## Performance Characteristics

### First Request (Cold Start)
- Time: 20-30 seconds
- Breakdown:
  - Embedding model loading: 10-15s
  - Vector search: 1-2s
  - LLM inference (Groq): 5-10s
  - Total: 20-30s

### Subsequent Requests (Warm)
- Time: 5-10 seconds
- Breakdown:
  - Embedding (cached model): <1s
  - Vector search: 1-2s
  - LLM inference: 3-7s
  - Total: 5-10s

### Concurrent Requests
- 3 concurrent requests: ~23s (vs 60-90s sequential)
- Demonstrates true async handling
- **Note**: System may become unresponsive after extended concurrent load

## Known Limitations

### 1. Stability Issues
- **Symptom**: Backend becomes unresponsive after multiple concurrent request cycles
- **Likely causes**:
  - Thread pool exhaustion
  - Database connection pool limits
  - Memory pressure from embedding model copies
- **Workaround**: Restart backend container when unresponsive
- **Future fix**: Implement proper connection pooling, resource cleanup, health monitoring

### 2. Response Parsing
- Some responses show "N/A" for response field
- Metrics are calculated correctly
- **Fix needed**: Check response field mapping in `ChatQueryResponse`

### 3. Memory Usage
- Embedding model: ~90MB per process
- Single worker mode: One copy loaded
- Multi-worker mode (tested, reverted): N workers × 90MB

## Recommendations

### Short Term
1. ✅ Use async fixes (already implemented)
2. ✅ Single-worker mode for stability
3. ⚠️ Monitor and restart backend if unresponsive
4. Add response field debugging

### Medium Term
1. Implement proper database connection pooling
2. Add health check endpoint with resource monitoring
3. Implement graceful degradation (queue requests when overloaded)
4. Add request timeout and retry logic
5. Fix response field parsing

### Long Term
1. Consider lighter embedding model (faster load, less memory)
2. Evaluate external embedding service (e.g., OpenAI) to eliminate local model
3. Implement Redis-based request queue for high concurrency
4. Add auto-restart on health check failure
5. Implement proper async database driver (e.g., asyncpg instead of psycopg2)

## Conclusion

✅ **Major improvement achieved**: The blocking issue is resolved. Concurrent requests now work.

⚠️ **Stability needs work**: System can handle concurrent requests but may become unresponsive after extended use.

✅ **Production-ready**: For low-to-medium traffic with monitoring and restart capability.

❌ **Not production-ready**: For high-traffic, mission-critical applications without further stability work.

## Testing Commands

```bash
# Test single query
python3 files/test_single_query.py

# Test concurrent requests
python3 files/test_concurrent_requests.py

# Restart backend if unresponsive
docker compose restart backend

# Check health
curl http://localhost:8000/health
```
