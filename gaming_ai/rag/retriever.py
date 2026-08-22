"""Semantic RAG retriever formatting grounded context for the companion LLM."""

from __future__ import annotations

import logging
from typing import List, Optional

from gaming_ai.rag.embeddings import BaseEmbeddingModel, OllamaEmbeddingModel
from gaming_ai.rag.vector_store import LocalVectorStore, SearchResult

logger = logging.getLogger("gaming_ai.rag.retriever")


class RAGRetriever:
    """Retrieves relevant game knowledge and formats grounded context with citations."""

    def __init__(
        self,
        vector_store: LocalVectorStore,
        embedding_model: Optional[BaseEmbeddingModel] = None,
        top_k: int = 3,
        min_similarity: float = 0.40,
    ) -> None:
        self.vector_store = vector_store
        self.embedding_model = embedding_model or OllamaEmbeddingModel()
        self.top_k = top_k
        self.min_similarity = min_similarity

    def _is_knowledge_query(self, text: str) -> bool:
        """Check if query is asking for game guide facts, stats, weaknesses, or mechanics."""
        lore_keywords = [
            "weak", "weakness", "weak against", "how to beat", "how do i beat",
            "boss", "strategy", "lore", "drop", "location", "recipe", "craft",
            "stat", "scaling", "build", "quest", "how to get", "where is",
            "guide", "tips", "best weapon", "talisman", "spell"
        ]
        lower = text.lower()
        return any(w in lower for w in lore_keywords)

    async def retrieve(
        self,
        query: str,
        game: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[SearchResult]:
        """Search vector store for top matching knowledge chunks."""
        k = top_k or self.top_k
        query_vec = await self.embedding_model.embed_text(query)
        results = self.vector_store.search(
            query_embedding=query_vec,
            top_k=k,
            game_filter=game,
            min_similarity=self.min_similarity,
        )
        return results

    async def retrieve_formatted_context(
        self,
        query: str,
        game: Optional[str] = None,
        top_k: Optional[int] = None,
        force: bool = False,
    ) -> Optional[str]:
        """
        Search for relevant facts and format them with source citations.
        Returns None if no relevant facts meet the similarity threshold.
        """
        if not force and not self._is_knowledge_query(query):
            return None

        results = await self.retrieve(query=query, game=game, top_k=top_k)
        if not results:
            return None

        formatted_parts = []
        for r in results:
            chunk = r.chunk
            citation = f"[Source: {chunk.source} | Section: {chunk.section} | Similarity: {r.similarity_score:.2f}]"
            formatted_parts.append(f"{citation}\n{chunk.text}")

        context_block = "RETRIEVED GAMEPLAY KNOWLEDGE (Use these facts to guide the player):\n" + "\n\n".join(formatted_parts)
        logger.info("RAG Retrieved %d knowledge chunks for query: '%s'", len(results), query)
        return context_block
