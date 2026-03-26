"""Pydantic models for book.json structure."""

from typing import List, Optional
from pydantic import BaseModel, Field


class Sentence(BaseModel):
    """A single sentence with timing and page info."""

    start: float = Field(description="Start time in seconds")
    end: float = Field(description="End time in seconds")
    text: str = Field(description="Sentence text content")
    page: int = Field(description="PDF page number (1-based)")
    confidence: float = Field(
        default=1.0, description="Whisper confidence (0-1)"
    )


class Book(BaseModel):
    """New format book.json structure."""

    id: str = Field(description="Format: level-{letter}/{book-name}")
    title: str = Field(description="Book title (title case)")
    level: str = Field(description="Reading level: aa, a-z, z1, z2")
    pdf: str = Field(default="book.pdf", description="PDF filename")
    video: Optional[str] = Field(
        default=None, description="Video filename or null"
    )
    audio: str = Field(default="audio.mp3", description="Audio filename")
    sentences: List[Sentence] = Field(default_factory=list)

    def to_json(self) -> str:
        """Serialize to JSON string with proper formatting."""
        return self.model_dump_json(indent=2)

    def save(self, path: str) -> None:
        """Save book.json to file."""
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)
