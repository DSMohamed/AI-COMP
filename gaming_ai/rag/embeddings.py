"""Embedding models for semantic search and vector retrieval."""

from __future__ import annotations

from abc import ABC, abstractmethod
import hashlib
import logging
from typing import List, Optional
import httpx
import numpy as np

logger = logging.getLogger("gaming_ai.rag.embeddings")


class BaseEmbeddingModel(ABC):
    """Abstract interface for text embedding models."""

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate a vector embedding for a single text string."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a batch of text strings."""
        pass


class OllamaEmbeddingModel(BaseEmbeddingModel):
    """Generates embeddings using local Ollama (e.g., nomic-embed-text)."""

    def __init__(
        self,
        model_name: str = "nomic-embed-text",
        host: str = "http://127.0.0.1:11434",
        timeout: float = 30.0,
    ) -> None:
        self.model_name = model_name
        self.host = host.rstrip("/")
        self.timeout = timeout

    async def embed_text(self, text: str) -> List[float]:
        """Generate vector embedding via Ollama API."""
        payload = {"model": self.model_name, "prompt": text}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                res = await client.post(f"{self.host}/api/embeddings", json=payload)
                res.raise_for_status()
                data = res.json()
                embedding = data.get("embedding", [])
                return embedding
            except Exception as e:
                logger.error("Failed to generate embedding from Ollama: %s", e)
                raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings sequentially or in batch."""
        results = []
        for t in texts:
            emb = await self.embed_text(t)
            results.append(emb)
        return results


class MockEmbeddingModel(BaseEmbeddingModel):
    """Deterministic mock embedding generator for fast offline testing."""

    def __init__(self, dimension: int = 64) -> None:
        self.dimension = dimension

    def _hash_to_vec(self, text: str) -> List[float]:
        """Produce a normalized deterministic pseudo-embedding from text hash."""
        seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) % (2**32)
        rng = np.random.RandomState(seed)
        vec = rng.randn(self.dimension).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec.tolist()

    async def embed_text(self, text: str) -> List[float]:
        return self._hash_to_vec(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_to_vec(t) for t in texts]
