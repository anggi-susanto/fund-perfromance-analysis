"""
Improved Vector Store with proper async/sync separation and resource management
"""
from typing import List, Dict, Any, Optional
import numpy as np
import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
import asyncio
from functools import lru_cache
from app.core.config import settings

# Global embedding model cache
_embeddings_cache = None


@lru_cache(maxsize=1)
def get_embeddings_model():
    """
    Get or create the embeddings model (cached singleton)
    Thread-safe singleton pattern
    """
    global _embeddings_cache
    
    if _embeddings_cache is not None:
        return _embeddings_cache
    
    provider = getattr(settings, 'EMBEDDING_PROVIDER', 'local')
    
    if provider == "openai" and settings.OPENAI_API_KEY:
        try:
            print("Loading OpenAI embeddings...")
            _embeddings_cache = OpenAIEmbeddings(
                model=settings.OPENAI_EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY
            )
            return _embeddings_cache
        except Exception as e:
            print(f"Failed to initialize OpenAI embeddings: {e}")
            print("Falling back to local embeddings...")
    
    # Fallback to local embeddings
    print("Loading local HuggingFace embeddings (this takes 10-30s on first load)...")
    _embeddings_cache = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    print("✓ Embeddings loaded and cached!")
    return _embeddings_cache


class VectorStore:
    """
    Improved pgvector-based vector store with proper resource management
    
    Key improvements:
    1. Accepts db session from caller (no session creation)
    2. Embeddings model is shared singleton
    3. Async operations properly isolated
    4. No resource leaks
    """
    
    def __init__(self, db: Session):
        """
        Initialize vector store with existing database session
        
        Args:
            db: SQLAlchemy database session (managed by caller)
        """
        if db is None:
            raise ValueError("Database session is required")
        
        self.db = db
        self.embeddings = get_embeddings_model()
        self._ensure_extension()
    
    def _ensure_extension(self):
        """Ensure pgvector extension is enabled"""
        try:
            self.db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
            # Determine dimension
            provider = getattr(settings, 'EMBEDDING_PROVIDER', 'local')
            dimension = 1536 if provider == "openai" and settings.OPENAI_API_KEY else 384
            
            # Create table if not exists
            create_table_sql = text(f"""
                CREATE TABLE IF NOT EXISTS document_embeddings (
                    id SERIAL PRIMARY KEY,
                    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                    fund_id INTEGER,
                    chunk_index INTEGER,
                    content TEXT NOT NULL,
                    embedding vector({dimension}),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.db.execute(create_table_sql)
            
            # Create index if not exists
            create_index_sql = text("""
                CREATE INDEX IF NOT EXISTS document_embeddings_vector_idx 
                ON document_embeddings 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
            self.db.execute(create_index_sql)
            
            self.db.commit()
            print(f"✓ Vector table created with dimension: {dimension}")
            
        except Exception as e:
            print(f"Error ensuring extension: {e}")
            self.db.rollback()
    
    async def add_documents(
        self, 
        texts: List[str], 
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[int]:
        """
        Add documents with embeddings to the vector store
        
        Args:
            texts: List of text chunks
            metadata: Optional metadata for each chunk
            
        Returns:
            List of inserted document IDs
        """
        if not texts:
            return []
        
        try:
            # Generate embeddings in thread pool (blocking operation)
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,  # Use default executor
                self._embed_texts_sync,
                texts
            )
            
            # Insert into database (in thread pool to avoid blocking)
            ids = await loop.run_in_executor(
                None,
                self._insert_embeddings_sync,
                texts,
                embeddings,
                metadata or [{}] * len(texts)
            )
            
            return ids
            
        except Exception as e:
            import traceback
            print(f"Error adding documents: {e}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            self.db.rollback()
            raise
    
    def _embed_texts_sync(self, texts: List[str]) -> List[List[float]]:
        """Synchronous embedding generation (runs in thread pool)"""
        if hasattr(self.embeddings, 'embed_documents'):
            return self.embeddings.embed_documents(texts)
        else:
            return [self.embeddings.encode(text).tolist() for text in texts]
    
    def _insert_embeddings_sync(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadata_list: List[Dict[str, Any]]
    ) -> List[int]:
        """Synchronous database insert (runs in thread pool)"""
        ids = []
        
        for text_content, embedding, metadata in zip(texts, embeddings, metadata_list):
            embedding_str = str(embedding)
            
            insert_sql = text("""
                INSERT INTO document_embeddings 
                (document_id, fund_id, chunk_index, content, embedding, metadata)
                VALUES (:document_id, :fund_id, :chunk_index, :content, 
                        CAST(:embedding AS vector), :metadata)
                RETURNING id
            """)
            
            result = self.db.execute(insert_sql, {
                "document_id": metadata.get("document_id"),
                "fund_id": metadata.get("fund_id"),
                "chunk_index": metadata.get("chunk_index", 0),
                "content": text_content,
                "embedding": embedding_str,
                "metadata": json.dumps(metadata)  # Convert to JSON string
            })
            
            row = result.fetchone()
            if row:
                ids.append(row[0])
        
        self.db.commit()
        return ids
    
    async def similarity_search(
        self, 
        query: str, 
        k: int = 5, 
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            k: Number of results
            filter_metadata: Optional filters
            
        Returns:
            List of similar documents with scores
        """
        try:
            # Generate query embedding in thread pool
            loop = asyncio.get_event_loop()
            query_embedding = await loop.run_in_executor(
                None,
                self._embed_query_sync,
                query
            )
            
            # Search database in thread pool
            results = await loop.run_in_executor(
                None,
                self._search_sync,
                query_embedding,
                k,
                filter_metadata
            )
            
            return results
            
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []
    
    def _embed_query_sync(self, query: str) -> List[float]:
        """Synchronous query embedding (runs in thread pool)"""
        if hasattr(self.embeddings, 'embed_query'):
            return self.embeddings.embed_query(query)
        else:
            return self.embeddings.encode(query).tolist()
    
    def _search_sync(
        self,
        query_embedding: List[float],
        k: int,
        filter_metadata: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Synchronous database search (runs in thread pool)"""
        embedding_str = str(query_embedding)
        
        # Build query with filters
        where_clause = ""
        if filter_metadata:
            conditions = []
            for key, value in filter_metadata.items():
                if key in ["document_id", "fund_id"]:
                    conditions.append(f"{key} = {value}")
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
        
        search_sql = text(f"""
            SELECT 
                id,
                document_id,
                fund_id,
                content,
                metadata,
                1 - (embedding <=> CAST(:embedding AS vector)) as similarity
            FROM document_embeddings
            {where_clause}
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :k
        """)
        
        result = self.db.execute(search_sql, {
            "embedding": embedding_str,
            "k": k
        })
        
        documents = []
        for row in result:
            documents.append({
                "id": row[0],
                "document_id": row[1],
                "fund_id": row[2],
                "content": row[3],
                "metadata": row[4],
                "score": float(row[5])
            })
        
        return documents
    
    def clear(self, fund_id: Optional[int] = None):
        """Clear vector store"""
        try:
            if fund_id:
                delete_sql = text("DELETE FROM document_embeddings WHERE fund_id = :fund_id")
                self.db.execute(delete_sql, {"fund_id": fund_id})
            else:
                delete_sql = text("DELETE FROM document_embeddings")
                self.db.execute(delete_sql)
            
            self.db.commit()
        except Exception as e:
            print(f"Error clearing vector store: {e}")
            self.db.rollback()
