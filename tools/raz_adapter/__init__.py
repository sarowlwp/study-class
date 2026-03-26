"""RAZ Resource Adapter - Convert resources to book.json format."""

__version__ = "1.0.0"

from .scanner import ResourceScanner, Resource
from .matcher import ResourceMatcher, MatchedBook
from .generator import BookGenerator
from .transcriber import WhisperTranscriber
from .normalizer import normalize_name, to_kebab_case, to_title_case

__all__ = [
    "ResourceScanner",
    "Resource",
    "ResourceMatcher",
    "MatchedBook",
    "BookGenerator",
    "WhisperTranscriber",
    "normalize_name",
    "to_kebab_case",
    "to_title_case",
]
