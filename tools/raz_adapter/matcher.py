"""Resource matcher for linking audio, video, and PDF by book name."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .scanner import Resource
from .normalizer import to_kebab_case, to_title_case


@dataclass
class MatchedBook:
    """A book with matched resources across types."""

    normalized_name: str
    title: str
    book_id: str
    level: str
    pdf: Optional[Path] = None
    audio: Optional[Path] = None
    video: Optional[Path] = None


class ResourceMatcher:
    """Match resources by normalized name."""

    def __init__(self, resources: List[Resource]):
        self.resources = resources

    def match_books(self) -> List[MatchedBook]:
        """Group resources by normalized name and create matched books."""
        # Group by normalized name (using match_key for O level)
        groups: Dict[str, List[Resource]] = {}
        for resource in self.resources:
            # Use match_key if available (for O level), otherwise use normalized name
            key = resource.match_key if resource.match_key else resource.normalized
            if key not in groups:
                groups[key] = []
            groups[key].append(resource)

        # Create matched books
        books = []
        for key, group in groups.items():
            # Must have at least PDF and audio
            pdf = self._find_by_type(group, "pdf")
            audio = self._find_by_type(group, "audio")

            if pdf and audio:
                # Use audio name for title if PDF has coded name (O level)
                if pdf.match_key:
                    title = to_title_case(audio.name)
                else:
                    title = to_title_case(pdf.name)
                book_id = to_kebab_case(title)
                level = pdf.level

                video = self._find_by_type(group, "video")

                books.append(
                    MatchedBook(
                        normalized_name=key,
                        title=title,
                        book_id=book_id,
                        level=level,
                        pdf=pdf.path,
                        audio=audio.path,
                        video=video.path if video else None,
                    )
                )

        return books

    def _find_by_type(
        self, resources: List[Resource], resource_type: str
    ) -> Optional[Resource]:
        """Find first resource of given type."""
        for r in resources:
            if r.resource_type == resource_type:
                return r
        return None

    def get_match_stats(self) -> dict:
        """Get statistics about matching."""
        books = self.match_books()
        total = len(books)
        with_video = sum(1 for b in books if b.video)
        return {
            "total_matched": total,
            "with_video": with_video,
            "without_video": total - with_video,
        }
