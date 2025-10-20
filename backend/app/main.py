"""
FastAPI main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.endpoints import documents, funds, chat, metrics

# Global instances to avoid reloading models on each request
_vector_store = None
_embeddings_loaded = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global _vector_store, _embeddings_loaded
    
    print("="*60)
    print("🚀 Starting Fund Performance Analysis System")
    print("="*60)
    
    # Note: Model preloading moved to first request due to async issues
    # Models will be cached after first use
    print("\n✓ Application ready! Models will load on first request.")
    print("="*60)
    
    yield
    
    # Shutdown
    print("\n👋 Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Fund Performance Analysis System API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(funds.router, prefix="/api/funds", tags=["funds"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Fund Performance Analysis System API",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "embeddings_loaded": _embeddings_loaded
    }


def get_vector_store():
    """Get the preloaded vector store instance (or create new one if not loaded)"""
    global _vector_store
    if _vector_store is not None:
        return _vector_store
    
    # Fallback: create new instance if not preloaded
    from app.services.vector_store import VectorStore
    from app.db.session import SessionLocal
    db = SessionLocal()
    return VectorStore(db)
