# 📚 Game-Specific RAG Knowledge Base

The Retrieval-Augmented Generation (RAG) subsystem provides the AI companion with accurate, grounded domain knowledge for any game without requiring fine-tuning. It retrieves boss strategies, item crafting recipes, hidden locations, and damage weakness data from local markdown guides.

---

## 🏛️ RAG Pipeline (Section 15–19 & 46–47 Compliance)

```
[ Game Guides / Wikis (knowledge/<game>/*.md) ]
                        │
                        ▼
            [ MarkdownChunker ]
(Semantic header parsing, category inference, section metadata)
                        │
                        ▼
       [ OllamaEmbeddingModel (nomic-embed-text) ]
                        │
                        ▼
       [ LocalVectorStore (ChromaDB / Cosine) ]
                        │
    ┌───────────────────┴───────────────────┐
    │                                       │
    ▼                                       ▼
[ Player Voice / Text Query ] ──► [ RAGRetriever ]
("What is Margit weak against?")           │
                               (Game filter: "elden_ring")
                                           │
                                           ▼
                           [ Grounded Knowledge Block ]
                      ("[Source: bosses.md] Margit is weak to Slash/Bleed")
                                           │
                                           ▼
                                 [ Context Aggregator ]
                                           │
                                           ▼
                                    [ Companion LLM ]
                   ("Hit him with bleed and jump attacks! Avoid holy damage.")
```

---

## 📂 Knowledge Directory Structure

Place your game guides and markdown wiki notes under the `knowledge/` directory:
```text
knowledge/
├── elden_ring/
│   ├── bosses.md
│   ├── weapons_scaling.md
│   └── talismans.md
├── minecraft/
│   ├── recipes.md
│   └── potions.md
└── general/
    └── fps_mechanics.md
```

---

## 🧩 Components

1. **Semantic Chunker (`gaming_ai.rag.chunking.MarkdownChunker`)**:
   * Parses `#`, `##`, `###` headings and preserves document hierarchy.
   * Auto-infers category (`boss`, `item`, `mechanics`, `build`, `quest`).
2. **Local Embeddings (`gaming_ai.rag.embeddings.OllamaEmbeddingModel`)**:
   * Uses local `nomic-embed-text` via Ollama API (`127.0.0.1:11434`).
3. **Vector Database (`gaming_ai.rag.vector_store.LocalVectorStore`)**:
   * Persistent ChromaDB collection (`data/chroma`) with cosine distance metrics.
   * Fast NumPy in-memory fallback for zero-dependency portability.
4. **Grounded Retriever (`gaming_ai.rag.retriever.RAGRetriever`)**:
   * Formats top matching chunks with explicit file & section citations.
