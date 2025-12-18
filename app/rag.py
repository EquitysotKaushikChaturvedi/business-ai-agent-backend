import logging
import numpy as np
import openai
from typing import List, Dict, Any
from app.core.config import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

# Temporary in-memory store for POC if FAISS/Redis fails
# Structure: { business_id: { "vectors": np.array, "texts": [], "metadata": [] } }
GLOBAL_VECTOR_STORE = {}

class RAGManager:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            logger.warning("No OPENAI_API_KEY. RAG will not work.")
            self.client = None

    async def embed_text(self, text: str) -> List[float]:
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(self._embed_sync, text)

    async def embed_query(self, text: str) -> List[float]:
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(self._embed_sync, text)

    def _embed_sync(self, text: str) -> List[float]:
        if not self.client:
            return []
        try:
            # OpenAI Embedding Model
            response = self.client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return []

    async def ingest_document(self, business_id: str, text: str, source: str):
        """
        Chunk and store document.
        """
        # Simple chunking by paragraphs or fixed size
        chunks = self._chunk_text(text)
        
        logger.info(f"Ingesting {len(chunks)} chunks for {business_id} from {source}")

        for chunk in chunks:
            vector = await self.embed_text(chunk)
            if vector:
                self._save_to_store(business_id, vector, chunk, {"source": source})

    async def search(self, business_id: str, query: str, top_k: int = 3) -> str:
        """
        Retrieve relevant context.
        """
        query_vec = await self.embed_query(query)
        if not query_vec:
            return ""

        results = self._search_store(business_id, query_vec, top_k)
        
        # Format context
        context = ""
        for res in results:
            context += f"---\nSource: {res['metadata']['source']}\nContent: {res['text']}\n"
        
        return context

    def _chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        # Very basic chunking. In production, use LangChain text splitters.
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    def _save_to_store(self, business_id: str, vector: List[float], text: str, metadata: Dict):
        # NOTE: Ideally implementation uses FAISS or Redis VSS here.
        # For this standalone POC without Docker complexity, we might use a simple in-memory dict 
        # backed by a file or just in-memory (per user request for POC).
        # We will implement a numpy cosine similarity search for reliability.
        
        if business_id not in GLOBAL_VECTOR_STORE:
            GLOBAL_VECTOR_STORE[business_id] = {
                "vectors": [],
                "texts": [],
                "metadata": []
            }
        
        GLOBAL_VECTOR_STORE[business_id]["vectors"].append(vector)
        GLOBAL_VECTOR_STORE[business_id]["texts"].append(text)
        GLOBAL_VECTOR_STORE[business_id]["metadata"].append(metadata)

    def _search_store(self, business_id: str, query_vec: List[float], top_k: int) -> List[Dict]:
        if business_id not in GLOBAL_VECTOR_STORE:
            return []
        
        store = GLOBAL_VECTOR_STORE[business_id]
        if not store["vectors"]:
            return []

        # Convert to numpy
        vectors = np.array(store["vectors"])
        query = np.array(query_vec)
        
        # Cosine similarity
        norm_vectors = np.linalg.norm(vectors, axis=1)
        norm_query = np.linalg.norm(query)
        
        if norm_query == 0:
            return []

        dot_products = np.dot(vectors, query)
        similarities = dot_products / (norm_vectors * norm_query)

        # Get top K indices
        # Check if we have less than top_k items
        k = min(top_k, len(similarities))
        top_indices = np.argsort(similarities)[-k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                "text": store["texts"][idx],
                "metadata": store["metadata"][idx],
                "score": similarities[idx]
            })
        
        return results

rag_manager = RAGManager()
