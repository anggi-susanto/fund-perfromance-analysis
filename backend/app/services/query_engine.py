"""
Improved Query Engine with proper async handling and resource management
"""
from typing import Dict, Any, List, Optional
import time
import asyncio
from functools import lru_cache
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
from app.services.vector_store import VectorStore
from app.services.metrics_calculator import MetricsCalculator
from sqlalchemy.orm import Session


@lru_cache(maxsize=1)
def get_llm():
    """
    Get or create LLM instance (cached singleton)
    This ensures LLM is initialized once and reused
    """
    provider = getattr(settings, 'LLM_PROVIDER', 'groq')
    
    if provider == "groq":
        groq_key = getattr(settings, 'GROQ_API_KEY', '')
        if groq_key:
            try:
                print(f"Initializing Groq LLM ({settings.GROQ_MODEL})...")
                from langchain_groq import ChatGroq
                return ChatGroq(
                    api_key=groq_key,
                    model=settings.GROQ_MODEL,
                    temperature=0
                )
            except Exception as e:
                print(f"Failed to initialize Groq: {e}")
    
    if provider == "openai" and settings.OPENAI_API_KEY:
        try:
            print("Initializing OpenAI LLM...")
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0,
                openai_api_key=settings.OPENAI_API_KEY
            )
        except Exception as e:
            print(f"Failed to initialize OpenAI: {e}")
    
    if provider == "ollama":
        try:
            print(f"Initializing Ollama LLM ({settings.OLLAMA_MODEL})...")
            return Ollama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL
            )
        except Exception as e:
            print(f"Failed to connect to Ollama: {e}")
    
    raise ValueError("No LLM configured! Please set GROQ_API_KEY, OPENAI_API_KEY, or configure Ollama")


class QueryEngine:
    """
    Improved RAG-based query engine
    
    Key improvements:
    1. Database session managed by caller (no leaks)
    2. LLM and embeddings are singletons (no repeated initialization)
    3. Proper async/sync separation with default executor
    4. No custom thread pools (uses asyncio default)
    """
    
    def __init__(self, db: Session):
        """
        Initialize query engine with database session
        
        Args:
            db: SQLAlchemy session (managed by caller via FastAPI dependency)
        """
        if db is None:
            raise ValueError("Database session is required")
        
        self.db = db
        self.vector_store = VectorStore(db)  # Pass session to VectorStore
        self.metrics_calculator = MetricsCalculator(db)
        self.llm = get_llm()  # Get cached LLM singleton
    
    async def process_query(
        self, 
        query: str, 
        fund_id: Optional[int] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process user query using RAG
        
        All blocking operations run in asyncio's default thread pool
        to avoid blocking the event loop
        """
        start_time = time.time()
        
        try:
            # Step 1: Classify query intent (fast, can be sync)
            intent = self._classify_intent_sync(query)
            
            # Step 2: Retrieve relevant context (async - uses thread pool internally)
            filter_metadata = {"fund_id": fund_id} if fund_id else None
            relevant_docs = await self.vector_store.similarity_search(
                query=query,
                k=settings.TOP_K_RESULTS,
                filter_metadata=filter_metadata
            )
            
            # Step 3: Get metrics (run in thread pool - blocking DB operation)
            metrics = None
            if fund_id and intent in ["calculation", "retrieval"]:
                loop = asyncio.get_event_loop()
                metrics = await loop.run_in_executor(
                    None,  # Use default executor
                    self.metrics_calculator.calculate_all_metrics,
                    fund_id
                )
            
            # Step 4: Generate response (run in thread pool - blocking LLM call)
            loop = asyncio.get_event_loop()
            answer = await loop.run_in_executor(
                None,
                self._generate_response_sync,
                query,
                relevant_docs,
                metrics,
                conversation_history or []
            )
            
            elapsed = time.time() - start_time
            
            return {
                "answer": answer,
                "sources": [
                    {
                        "content": doc["content"][:200],
                        "document_id": doc.get("document_id"),
                        "score": doc.get("score")
                    }
                    for doc in relevant_docs[:3]
                ],
                "metrics": metrics,
                "processing_time": round(elapsed, 2)
            }
            
        except Exception as e:
            print(f"Error processing query: {e}")
            import traceback
            traceback.print_exc()
            return {
                "answer": f"I apologize, but I encountered an error: {str(e)}",
                "sources": [],
                "metrics": None,
                "processing_time": round(time.time() - start_time, 2)
            }
    
    def _classify_intent_sync(self, query: str) -> str:
        """Classify query intent (synchronous, fast operation)"""
        query_lower = query.lower()
        
        # Calculation keywords
        if any(word in query_lower for word in ["calculate", "compute", "what is the", "dpi", "irr", "tvpi", "moic", "pic"]):
            return "calculation"
        
        # Retrieval keywords
        if any(word in query_lower for word in ["show", "list", "get", "find", "retrieve", "capital call", "distribution"]):
            return "retrieval"
        
        # Definition keywords
        if any(word in query_lower for word in ["what is", "define", "explain", "meaning"]):
            return "definition"
        
        return "general"
    
    def _generate_response_sync(
        self,
        query: str,
        context: List[Dict[str, Any]],
        metrics: Optional[Dict[str, Any]],
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Generate LLM response (synchronous, runs in thread pool)
        
        This method is called from thread pool executor, so it's safe
        to do blocking operations here
        """
        # Build context string
        context_str = "\n\n".join([
            f"[Source {i+1}]\n{doc['content']}"
            for i, doc in enumerate(context[:3])
        ])
        
        # Build metrics string
        metrics_str = ""
        if metrics:
            metrics_str = "\n\nAvailable Metrics:\n"
            for key, value in metrics.items():
                if value is not None:
                    metrics_str += f"- {key.upper()}: {value}\n"
        
        # Build conversation history
        history_str = ""
        if conversation_history:
            history_str = "\n\nPrevious Conversation:\n"
            for msg in conversation_history[-3:]:
                history_str += f"{msg['role']}: {msg['content']}\n"
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a financial analyst assistant specializing in private equity fund performance.

Your role:
- Answer questions about fund performance using provided context
- Calculate metrics like DPI, IRR when asked
- Explain complex financial terms in simple language
- Always cite your sources from the provided documents

When calculating:
- Use the provided metrics data
- Show your work step-by-step
- Explain any assumptions made

Format your responses:
- Be concise but thorough
- Use bullet points for lists
- Bold important numbers using **number**
- Provide context for metrics"""),
            ("user", """Context from documents:
{context}
{metrics}
{history}

Question: {query}

Please provide a helpful answer based on the context and metrics provided.""")
        ])
        
        # Generate response (blocking operation, but we're in thread pool)
        messages = prompt.format_messages(
            context=context_str,
            metrics=metrics_str,
            history=history_str,
            query=query
        )
        
        try:
            response = self.llm.invoke(messages)
            if hasattr(response, 'content'):
                return response.content
            return str(response)
        except Exception as e:
            return f"I apologize, but I encountered an error generating a response: {str(e)}"
