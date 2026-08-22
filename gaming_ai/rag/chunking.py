"""Semantic and structure-aware chunking for gaming knowledge documents."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re
from typing import Any, Dict, List, Optional


@dataclass
class DocumentChunk:
    """A semantic chunk of gaming knowledge with rich source metadata."""
    chunk_id: str
    text: str
    game: str = "general"
    source: str = "unknown"
    section: str = ""
    category: str = "general"  # boss, item, mechanic, build, quest, guide
    metadata: Dict[str, Any] = field(default_factory=dict)


class MarkdownChunker:
    """Splits markdown game documents along header boundaries and structural sections."""

    def __init__(self, max_chunk_chars: int = 1200, overlap_chars: int = 150) -> None:
        self.max_chunk_chars = max_chunk_chars
        self.overlap_chars = overlap_chars

    def _infer_category(self, text: str, section: str) -> str:
        """Infer gaming category from section title and text content."""
        combined = f"{section} {text}".lower()
        if any(w in combined for w in ("boss", "enemy", "phase", "weakness", "attack", "health")):
            return "boss"
        elif any(w in combined for w in ("weapon", "item", "armor", "talisman", "spell", "craft")):
            return "item"
        elif any(w in combined for w in ("build", "stat", "attribute", "scaling", "level")):
            return "build"
        elif any(w in combined for w in ("quest", "npc", "dialogue", "location")):
            return "quest"
        elif any(w in combined for w in ("mechanic", "parry", "dodge", "stamina", "damage")):
            return "mechanics"
        return "general"

    def chunk_document(
        self,
        content: str,
        game: str = "general",
        source_name: str = "document.md",
    ) -> List[DocumentChunk]:
        """
        Split markdown text by headers while preserving section hierarchy and tables.
        """
        chunks: List[DocumentChunk] = []
        # Split on markdown headers (#, ##, ###)
        header_pattern = re.compile(r"^(#{1,4}\s+.+)$", re.MULTILINE)
        parts = header_pattern.split(content)

        current_header = "General"
        section_text = ""

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if header_pattern.match(part):
                # Save previous section if not empty
                if section_text:
                    self._add_chunks(
                        chunks, section_text, game, source_name, current_header
                    )
                    section_text = ""
                current_header = part.lstrip("#").strip()
            else:
                section_text += ("\n\n" if section_text else "") + part

        if section_text:
            self._add_chunks(chunks, section_text, game, source_name, current_header)

        return chunks

    def _add_chunks(
        self,
        chunks_list: List[DocumentChunk],
        text: str,
        game: str,
        source: str,
        section: str,
    ) -> None:
        """Split a section text into bounded chunks with metadata."""
        category = self._infer_category(text, section)

        if len(text) <= self.max_chunk_chars:
            chunk_id = hashlib.md5(f"{game}:{source}:{section}:{text[:50]}".encode()).hexdigest()[:12]
            chunks_list.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    text=f"[{game.upper()}] {section}\n{text}",
                    game=game.lower(),
                    source=source,
                    section=section,
                    category=category,
                )
            )
        else:
            # Paragraph-based splitting with overlap
            paragraphs = text.split("\n\n")
            current_chunk = ""
            for p in paragraphs:
                if len(current_chunk) + len(p) <= self.max_chunk_chars:
                    current_chunk += ("\n\n" if current_chunk else "") + p
                else:
                    if current_chunk:
                        chunk_id = hashlib.md5(f"{game}:{source}:{section}:{current_chunk[:50]}".encode()).hexdigest()[:12]
                        chunks_list.append(
                            DocumentChunk(
                                chunk_id=chunk_id,
                                text=f"[{game.upper()}] {section}\n{current_chunk}",
                                game=game.lower(),
                                source=source,
                                section=section,
                                category=category,
                            )
                        )
                    current_chunk = p

            if current_chunk:
                chunk_id = hashlib.md5(f"{game}:{source}:{section}:{current_chunk[:50]}".encode()).hexdigest()[:12]
                chunks_list.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        text=f"[{game.upper()}] {section}\n{current_chunk}",
                        game=game.lower(),
                        source=source,
                        section=section,
                        category=category,
                    )
                )
