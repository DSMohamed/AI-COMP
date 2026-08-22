"""Knowledge ingestion pipeline for game guides and wiki documents."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from gaming_ai.rag.chunking import DocumentChunk, MarkdownChunker
from gaming_ai.rag.embeddings import BaseEmbeddingModel, OllamaEmbeddingModel
from gaming_ai.rag.vector_store import LocalVectorStore

logger = logging.getLogger("gaming_ai.rag.ingestion")


class KnowledgeIngestor:
    """Discovers, parses, embeds, and indexes game knowledge documents."""

    def __init__(
        self,
        vector_store: LocalVectorStore,
        embedding_model: Optional[BaseEmbeddingModel] = None,
        chunker: Optional[MarkdownChunker] = None,
    ) -> None:
        self.vector_store = vector_store
        self.embedding_model = embedding_model or OllamaEmbeddingModel()
        self.chunker = chunker or MarkdownChunker()

    async def ingest_file(self, file_path: str | Path, game: Optional[str] = None) -> int:
        """
        Ingest a single markdown or text guide.
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning("File not found: %s", path)
            return 0

        game_name = game or path.parent.name
        if game_name in ("knowledge", ".", ""):
            game_name = "general"

        logger.info("Ingesting document: %s (Game: %s)", path.name, game_name)
        content = path.read_text(encoding="utf-8")

        chunks = self.chunker.chunk_document(
            content=content,
            game=game_name,
            source_name=path.name,
        )

        if not chunks:
            return 0

        # Generate embeddings
        texts = [c.text for c in chunks]
        embeddings = await self.embedding_model.embed_batch(texts)

        self.vector_store.add_chunks(chunks, embeddings)
        return len(chunks)

    async def ingest_directory(self, base_dir: str | Path = "knowledge") -> int:
        """
        Scan a knowledge directory structure (e.g. knowledge/elden_ring/*.md) and ingest all documents.
        """
        path = Path(base_dir)
        if not path.exists():
            logger.debug("Knowledge directory '%s' does not exist", base_dir)
            return 0

        total_chunks = 0
        for file in path.rglob("*"):
            if file.is_file() and file.suffix.lower() in (".md", ".txt", ".markdown"):
                # Determine game from subfolder name
                game = file.parent.name if file.parent != path else "general"
                chunks_count = await self.ingest_file(file, game=game)
                total_chunks += chunks_count

        logger.info("Knowledge ingestion complete: %d chunks indexed from '%s'", total_chunks, base_dir)
        return total_chunks
