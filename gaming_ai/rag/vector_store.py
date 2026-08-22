"""Embedded vector store for gaming knowledge retrieval."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from gaming_ai.rag.chunking import DocumentChunk

logger = logging.getLogger("gaming_ai.rag.vector_store")


@dataclass
class SearchResult:
    """A retrieved knowledge chunk with relevance score."""
    chunk: DocumentChunk
    similarity_score: float  # 0.0 to 1.0 (higher = more relevant)


class LocalVectorStore:
    """Persistent embedded vector storage powered by ChromaDB with cosine fallback."""

    def __init__(
        self,
        persist_directory: Optional[str | Path] = "data/chroma",
        collection_name: str = "gaming_knowledge",
    ) -> None:
        self.persist_directory = str(persist_directory) if persist_directory else None
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._in_memory_docs: List[DocumentChunk] = []
        self._in_memory_embeddings: List[np.ndarray] = []

    def _get_collection(self):
        """Lazy-load ChromaDB collection."""
        if self._collection is None:
            try:
                import chromadb
                if self.persist_directory:
                    Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
                    self._client = chromadb.PersistentClient(path=self.persist_directory)
                else:
                    self._client = chromadb.Client()

                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info("ChromaDB vector store initialized (collection: %s)", self.collection_name)
            except Exception as e:
                logger.warning("ChromaDB failed to initialize: %s. Using NumPy in-memory fallback.", e)
                self._collection = False
        return self._collection

    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        """Add document chunks and their precomputed embeddings to the vector store."""
        if not chunks:
            return

        collection = self._get_collection()
        if collection:
            ids = [c.chunk_id for c in chunks]
            documents = [c.text for c in chunks]
            metadatas = [
                {
                    "game": c.game,
                    "source": c.source,
                    "section": c.section,
                    "category": c.category,
                }
                for c in chunks
            ]
            collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            logger.info("Indexed %d chunks into ChromaDB", len(chunks))
        else:
            # In-memory fallback
            for c, emb in zip(chunks, embeddings):
                self._in_memory_docs.append(c)
                vec = np.array(emb, dtype=np.float32)
                norm = np.linalg.norm(vec)
                self._in_memory_embeddings.append(vec / norm if norm > 0 else vec)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        game_filter: Optional[str] = None,
        min_similarity: float = 0.40,
    ) -> List[SearchResult]:
        """
        Query vector store for top matching knowledge chunks.
        """
        collection = self._get_collection()
        results: List[SearchResult] = []

        if collection:
            where_filter = {"game": game_filter.lower()} if game_filter else None
            try:
                res = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where_filter,
                    include=["documents", "metadatas", "distances"],
                )

                if res and res["ids"] and len(res["ids"][0]) > 0:
                    for i in range(len(res["ids"][0])):
                        doc_id = res["ids"][0][i]
                        doc_text = res["documents"][0][i]
                        meta = res["metadatas"][0][i]
                        # In cosine space, distance is 1 - similarity
                        dist = res["distances"][0][i] if res["distances"] else 0.5
                        similarity = max(0.0, min(1.0, 1.0 - dist))

                        if similarity >= min_similarity:
                            chunk = DocumentChunk(
                                chunk_id=doc_id,
                                text=doc_text,
                                game=meta.get("game", "general"),
                                source=meta.get("source", "unknown"),
                                section=meta.get("section", ""),
                                category=meta.get("category", "general"),
                            )
                            results.append(SearchResult(chunk=chunk, similarity_score=round(similarity, 3)))
            except Exception as e:
                logger.error("ChromaDB query error: %s", e)
        else:
            # NumPy in-memory fallback search
            if not self._in_memory_embeddings:
                return []

            q_vec = np.array(query_embedding, dtype=np.float32)
            q_norm = np.linalg.norm(q_vec)
            if q_norm > 0:
                q_vec /= q_norm

            scores = [float(np.dot(q_vec, d_vec)) for d_vec in self._in_memory_embeddings]
            sorted_indices = np.argsort(scores)[::-1]

            for idx in sorted_indices[:top_k]:
                score = scores[idx]
                chunk = self._in_memory_docs[idx]
                if game_filter and chunk.game != game_filter.lower():
                    continue
                if score >= min_similarity:
                    results.append(SearchResult(chunk=chunk, similarity_score=round(score, 3)))

        return results

    def clear(self) -> None:
        """Clear all stored embeddings."""
        if self._collection and self._client:
            try:
                self._client.delete_collection(self.collection_name)
                self._collection = None
            except Exception as e:
                logger.debug("Error clearing ChromaDB: %s", e)
        self._in_memory_docs.clear()
        self._in_memory_embeddings.clear()
