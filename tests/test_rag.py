"""Tests for RAG chunking, vector storage, ingestion, and knowledge retrieval."""

from pathlib import Path
import pytest
from gaming_ai.agent.agent import GamingCompanionAgent
from gaming_ai.app.config import AppConfig
from gaming_ai.models.provider import MockLLMProvider
from gaming_ai.rag.chunking import MarkdownChunker
from gaming_ai.rag.embeddings import MockEmbeddingModel
from gaming_ai.rag.ingestion import KnowledgeIngestor
from gaming_ai.rag.retriever import RAGRetriever
from gaming_ai.rag.vector_store import LocalVectorStore


def test_markdown_chunker() -> None:
    """Verify semantic header splitting and category inference."""
    chunker = MarkdownChunker(max_chunk_chars=300)
    sample_doc = """# Boss Guide
## Margit Weaknesses
Margit is weak to Slash damage and Bleed. Avoid holy weapons.

## Radahn Strategy
Use torrent to dodge gravity arrows. Summon festival warriors.
"""
    chunks = chunker.chunk_document(sample_doc, game="elden_ring", source_name="guide.md")
    assert len(chunks) >= 2
    assert chunks[0].game == "elden_ring"
    assert chunks[0].category == "boss"
    assert "Margit" in chunks[0].text


@pytest.mark.asyncio
async def test_vector_store_and_retriever() -> None:
    """Verify vector search and formatted context retrieval with citations."""
    vector_store = LocalVectorStore(persist_directory=None, collection_name="test_collection")
    embedding_model = MockEmbeddingModel(dimension=32)
    ingestor = KnowledgeIngestor(
        vector_store=vector_store,
        embedding_model=embedding_model,
    )

    doc_content = """# Elden Ring Strategy
## Margit Weakness
Margit the Fell Omen is weak to Bleed and Slash damage. Use Margit Shackle to stun him.
"""
    chunker = MarkdownChunker()
    chunks = chunker.chunk_document(doc_content, game="elden_ring", source_name="bosses.md")
    embeddings = await embedding_model.embed_batch([c.text for c in chunks])
    vector_store.add_chunks(chunks, embeddings)

    retriever = RAGRetriever(
        vector_store=vector_store,
        embedding_model=embedding_model,
        top_k=2,
        min_similarity=0.0,
    )

    # Test knowledge query formatting
    formatted_ctx = await retriever.retrieve_formatted_context(
        query="What is Margit weak against?",
        game="elden_ring",
        force=True,
    )
    assert formatted_ctx is not None
    assert "RETRIEVED GAMEPLAY KNOWLEDGE" in formatted_ctx
    assert "bosses.md" in formatted_ctx


@pytest.mark.asyncio
async def test_agent_rag_integration() -> None:
    """Verify companion agent queries RAG and includes knowledge in prompt."""
    vector_store = LocalVectorStore(persist_directory=None, collection_name="test_agent_rag")
    embedding_model = MockEmbeddingModel(dimension=32)
    
    chunker = MarkdownChunker()
    chunks = chunker.chunk_document(
        "# Boss Guide\n## Malenia Strategy\nUse Fire and Frostbite against Malenia.",
        game="elden_ring",
        source_name="malenia.md",
    )
    embeddings = await embedding_model.embed_batch([c.text for c in chunks])
    vector_store.add_chunks(chunks, embeddings)

    retriever = RAGRetriever(
        vector_store=vector_store,
        embedding_model=embedding_model,
        top_k=1,
        min_similarity=0.0,
    )

    mock_llm = MockLLMProvider(canned_response="Hit her with Fire and Frost pots, easy win.")
    agent = GamingCompanionAgent(
        config=AppConfig(),
        llm_provider=mock_llm,
        retriever=retriever,
    )
    agent.context.current_game = "elden_ring"

    reply = await agent.respond_to_text("What is Malenia's weakness?", speak=False)
    assert "Fire" in reply or "Frost" in reply
    assert agent.context.latest_rag_context is not None
    assert "malenia.md" in agent.context.latest_rag_context
