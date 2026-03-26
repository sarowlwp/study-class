# RAZ Resource Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI tool that converts RAZ learning resources (audio, video, PDF) into a new book.json format with sentence-level timestamps using faster-whisper.

**Architecture:** The tool follows a pipeline pattern: Scanner discovers resources, Matcher links audio/video/PDF by normalized book names, Transcriber generates timestamps with Whisper, and Generator assembles the final book.json with copied assets.

**Tech Stack:** Python 3.10+, faster-whisper, pydantic, click, tqdm

---

## File Structure

```
tools/
├── raz_adapter/
│   ├── __init__.py          # Package exports
│   ├── models.py            # Pydantic models for Book, Sentence
│   ├── normalizer.py        # Book name normalization (strip prefixes, lowercase)
│   ├── scanner.py           # Resource discovery across PDF/audio/video dirs
│   ├── matcher.py           # Match resources by normalized name
│   ├── transcriber.py       # Whisper ASR with word-level timestamps
│   ├── generator.py         # book.json creation and asset copying
│   └── cli.py               # Click command-line interface
├── requirements.txt         # Python dependencies
tests/
├── fixtures/                # Test audio/PDF files
├── test_normalizer.py
├── test_matcher.py
└── test_transcriber.py
```

---

## Task 1: Project Setup and Dependencies

**Files:**
- Create: `tools/requirements.txt`
- Create: `tools/raz_adapter/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```txt
faster-whisper>=0.10.0
pydantic>=2.0.0
click>=8.0.0
tqdm>=4.65.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

- [ ] **Step 2: Install dependencies**

```bash
cd tools && pip install -r requirements.txt
```

Expected: All packages install successfully (faster-whisper downloads ~466MB for small model)

- [ ] **Step 3: Create package init (minimal)**

Create `tools/raz_adapter/__init__.py`:

```python
"""RAZ Resource Adapter - Convert resources to book.json format."""

__version__ = "1.0.0"
```

- [ ] **Step 4: Create test infrastructure**

Create `tests/__init__.py`:
```bash
touch tests/__init__.py
```

Create `pytest.ini` in project root:
```ini
[pytest]
pythonpath = tools
```

- [ ] **Step 5: Commit setup**

```bash
git add tools/requirements.txt tools/raz_adapter/__init__.py tests/__init__.py pytest.ini
git commit -m "chore: setup RAZ adapter project structure and dependencies"
```

---

## Task 2: Pydantic Models

**Files:**
- Create: `tools/raz_adapter/models.py`

- [ ] **Step 1: Write the models**

Create `tools/raz_adapter/models.py`:

```python
"""Pydantic models for book.json structure."""

from typing import Optional
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
    sentences: list[Sentence] = Field(default_factory=list)

    def to_json(self) -> str:
        """Serialize to JSON string with proper formatting."""
        return self.model_dump_json(indent=2)

    def save(self, path: str) -> None:
        """Save book.json to file."""
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)
```

- [ ] **Step 2: Create test file**

Create `tests/test_models.py`:

```python
"""Tests for pydantic models."""

import json
import pytest
from raz_adapter.models import Sentence, Book


class TestSentence:
    def test_create_sentence(self):
        s = Sentence(start=0.5, end=3.2, text="Hello world.", page=1)
        assert s.start == 0.5
        assert s.end == 3.2
        assert s.text == "Hello world."
        assert s.page == 1
        assert s.confidence == 1.0

    def test_sentence_with_confidence(self):
        s = Sentence(
            start=0.5, end=3.2, text="Hello.", page=1, confidence=0.95
        )
        assert s.confidence == 0.95


class TestBook:
    def test_create_book(self):
        book = Book(
            id="level-e/arctic-animals",
            title="Arctic Animals",
            level="e",
            sentences=[
                Sentence(start=0.5, end=3.2, text="Arctic Animals.", page=1)
            ],
        )
        assert book.id == "level-e/arctic-animals"
        assert book.title == "Arctic Animals"
        assert book.level == "e"
        assert len(book.sentences) == 1

    def test_book_defaults(self):
        book = Book(id="level-a/test", title="Test", level="a")
        assert book.pdf == "book.pdf"
        assert book.audio == "audio.mp3"
        assert book.video is None

    def test_book_to_json(self):
        book = Book(
            id="level-e/test",
            title="Test",
            level="e",
            sentences=[Sentence(start=0, end=1, text="Hi.", page=1)],
        )
        json_str = book.to_json()
        data = json.loads(json_str)
        assert data["id"] == "level-e/test"
        assert data["title"] == "Test"
        assert len(data["sentences"]) == 1
```

- [ ] **Step 3: Run tests to verify**

```bash
python -m pytest tests/test_models.py -v
```

Expected: All 5 tests pass

- [ ] **Step 4: Commit**

```bash
git add tools/raz_adapter/models.py tests/test_models.py
git commit -m "feat(models): add Book and Sentence pydantic models"
```

---

## Task 3: Name Normalizer

**Files:**
- Create: `tools/raz_adapter/normalizer.py`

- [ ] **Step 1: Write the normalizer**

Create `tools/raz_adapter/normalizer.py`:

```python
"""Book name normalization for matching across resource types."""

import re


def normalize_name(name: str) -> str:
    """
    Normalize book name for matching.

    Args:
        name: Raw filename like "01 arctic animals.mp3" or
              "E-01Arctic Animals.mp4"

    Returns:
        Normalized lowercase string like "arcticanimals"

    Examples:
        >>> normalize_name("01 arctic animals.mp3")
        'arcticanimals'
        >>> normalize_name("E-01Arctic Animals.mp4")
        'arcticanimals'
        >>> normalize_name("04places plants and animals live.mp3")
        'placesplantsandanimalslive'
    """
    # Remove file extension
    name = re.sub(r"\.[^.]+$", "", name)

    # Remove leading numbers and separators: "01 ", "E-01", "E-02"
    name = re.sub(r"^[A-Z]?\d+[\s\-]", "", name)

    # Remove non-alphanumeric (except spaces for now)
    name = re.sub(r"[^\w\s]", "", name)

    # Normalize to lowercase
    name = name.lower()

    # Remove leading digits that might remain
    name = re.sub(r"^\d+", "", name)

    # Compress whitespace
    name = re.sub(r"\s+", "", name)

    return name


def to_kebab_case(title: str) -> str:
    """
    Convert title to kebab-case for IDs.

    Args:
        title: Book title like "Arctic Animals"

    Returns:
        kebab-case string like "arctic-animals"
    """
    # Remove non-alphanumeric except spaces
    name = re.sub(r"[^\w\s]", "", title)
    # Normalize spaces and convert to lowercase
    name = re.sub(r"\s+", "-", name.strip()).lower()
    # Remove leading/trailing dashes
    name = name.strip("-")
    return name


def to_title_case(name: str) -> str:
    """
    Convert normalized name to title case for display.

    Args:
        name: String like "arctic animals"

    Returns:
        Title case string like "Arctic Animals"
    """
    # First normalize to remove any remaining artifacts
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name.strip())
    return name.title()
```

- [ ] **Step 2: Create tests**

Create `tests/test_normalizer.py`:

```python
"""Tests for name normalizer."""

import pytest
from raz_adapter.normalizer import normalize_name, to_kebab_case, to_title_case


class TestNormalizeName:
    def test_audio_with_number_prefix(self):
        assert normalize_name("01 arctic animals.mp3") == "arcticanimals"

    def test_audio_without_space(self):
        assert normalize_name("04places plants and animals live.mp3") == "placesplantsandanimalslive"

    def test_video_with_level_prefix(self):
        assert normalize_name("E-01Arctic Animals.mp4") == "arcticanimals"

    def test_pdf_simple(self):
        assert normalize_name("Arctic Animals.pdf") == "arcticanimals"

    def test_with_apostrophe(self):
        assert normalize_name("What's That.mp3") == "whatsthat"

    def test_multiple_spaces(self):
        assert normalize_name("All   About   Orcas.mp3") == "allaboutorcas"

    def test_no_extension(self):
        assert normalize_name("arctic animals") == "arcticanimals"


class TestToKebabCase:
    def test_simple_title(self):
        assert to_kebab_case("Arctic Animals") == "arctic-animals"

    def test_multiple_words(self):
        assert to_kebab_case("All About Orcas") == "all-about-orcas"

    def test_extra_spaces(self):
        assert to_kebab_case("  Arctic   Animals  ") == "arctic-animals"


class TestToTitleCase:
    def test_normalized_name(self):
        assert to_title_case("arctic animals") == "Arctic Animals"

    def test_with_artifacts(self):
        assert to_title_case("arctic-animals") == "Arctic Animals"
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/test_normalizer.py -v
```

Expected: All 11 tests pass

- [ ] **Step 4: Commit**

```bash
git add tools/raz_adapter/normalizer.py tests/test_normalizer.py
git commit -m "feat(normalizer): add book name normalization functions"
```

---

## Task 4: Resource Scanner

**Files:**
- Create: `tools/raz_adapter/scanner.py`

- [ ] **Step 1: Write the scanner**

Create `tools/raz_adapter/scanner.py`:

```python
"""Resource scanner for discovering PDF, audio, and video files."""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from .normalizer import normalize_name


@dataclass
class Resource:
    """A discovered resource file."""

    path: Path
    name: str
    normalized: str
    level: str
    resource_type: str  # "pdf", "audio", "video"


class ResourceScanner:
    """Scan raz-resourcer directory for resources."""

    LEVEL_MAP = {
        "AA": "aa",
        "A": "a",
        "B": "b",
        "C": "c",
        "D": "d",
        "E": "e",
        "F": "f",
        "G": "g",
        "H": "h",
        "I": "i",
        "J": "j",
        "K": "k",
        "L": "l",
        "M": "m",
        "N": "n",
        "O": "o",
        "P": "p",
        "Q": "q",
        "R": "r",
        "S": "s",
        "T": "t",
        "U": "u",
        "V": "v",
        "W": "w",
        "X": "x",
        "Y": "y",
        "Z": "z",
        "Z①": "z1",
        "Z②": "z2",
    }

    def __init__(self, base_dir: Path | str):
        self.base_dir = Path(base_dir)

    def _parse_level_dir(self, dir_name: str) -> Optional[str]:
        """Parse level code from directory name like 'E级音频' -> 'e'."""
        for prefix, code in self.LEVEL_MAP.items():
            if dir_name.startswith(f"{prefix}级") or dir_name.startswith(prefix):
                return code
        return None

    def scan_pdfs(self, level: Optional[str] = None) -> list[Resource]:
        """Scan for PDF files."""
        pdf_dir = self.base_dir / "RAZ-pdf点读版"
        resources = []

        for level_dir in pdf_dir.iterdir():
            if not level_dir.is_dir():
                continue

            dir_level = self._parse_level_dir(level_dir.name)
            if dir_level is None:
                continue
            if level and dir_level != level.lower():
                continue

            for pdf_file in level_dir.glob("*.pdf"):
                name = pdf_file.stem
                resources.append(Resource(
                    path=pdf_file,
                    name=name,
                    normalized=normalize_name(name),
                    level=dir_level,
                    resource_type="pdf",
                ))

        return resources

    def scan_audio(self, level: Optional[str] = None) -> list[Resource]:
        """Scan for audio files."""
        audio_base = self.base_dir / "RAZ AA级-Z音频"
        resources = []

        for level_dir in audio_base.iterdir():
            if not level_dir.is_dir():
                continue

            dir_level = self._parse_level_dir(level_dir.name)
            if dir_level is None:
                continue
            if level and dir_level != level.lower():
                continue

            for audio_file in level_dir.glob("*.mp3"):
                name = audio_file.stem
                resources.append(Resource(
                    path=audio_file,
                    name=name,
                    normalized=normalize_name(name),
                    level=dir_level,
                    resource_type="audio",
                ))

        return resources

    def scan_video(self, level: Optional[str] = None) -> list[Resource]:
        """Scan for video files."""
        video_base = self.base_dir / "RAZ视频"
        resources = []

        for level_dir in video_base.iterdir():
            if not level_dir.is_dir():
                continue

            dir_level = self._parse_level_dir(level_dir.name)
            if dir_level is None:
                continue
            if level and dir_level != level.lower():
                continue

            for video_file in level_dir.glob("*.mp4"):
                name = video_file.stem
                resources.append(Resource(
                    path=video_file,
                    name=name,
                    normalized=normalize_name(name),
                    level=dir_level,
                    resource_type="video",
                ))

        return resources

    def scan_all(
        self, level: Optional[str] = None
    ) -> tuple[list[Resource], list[Resource], list[Resource]]:
        """Scan all resource types."""
        return (
            self.scan_pdfs(level),
            self.scan_audio(level),
            self.scan_video(level),
        )
```

- [ ] **Step 2: Create tests**

Create `tests/test_scanner.py`:

```python
"""Tests for resource scanner."""

import pytest
from pathlib import Path
from raz_adapter.scanner import ResourceScanner, Resource


class TestResourceScanner:
    def test_parse_level_dir(self):
        scanner = ResourceScanner("/fake")
        assert scanner._parse_level_dir("E级音频") == "e"
        assert scanner._parse_level_dir("AA级音频") == "aa"
        assert scanner._parse_level_dir("Z①级") == "z1"
        assert scanner._parse_level_dir("Z②级") == "z2"

    def test_scan_pdfs_finds_files(self, tmp_path):
        # Setup test directory structure
        pdf_dir = tmp_path / "RAZ-pdf点读版" / "E.PDF"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "Arctic Animals.pdf").write_text("fake")
        (pdf_dir / "All About Orcas.pdf").write_text("fake")

        scanner = ResourceScanner(tmp_path)
        pdfs = scanner.scan_pdfs()

        assert len(pdfs) == 2
        assert all(p.resource_type == "pdf" for p in pdfs)
        assert any(p.normalized == "arcticanimals" for p in pdfs)

    def test_scan_audio_finds_files(self, tmp_path):
        audio_dir = tmp_path / "RAZ AA级-Z音频" / "E级音频"
        audio_dir.mkdir(parents=True)
        (audio_dir / "01 arctic animals.mp3").write_text("fake")

        scanner = ResourceScanner(tmp_path)
        audio = scanner.scan_audio()

        assert len(audio) == 1
        assert audio[0].normalized == "arcticanimals"
        assert audio[0].level == "e"

    def test_scan_video_finds_files(self, tmp_path):
        video_dir = tmp_path / "RAZ视频" / "E级视频"
        video_dir.mkdir(parents=True)
        (video_dir / "E-01Arctic Animals.mp4").write_text("fake")

        scanner = ResourceScanner(tmp_path)
        videos = scanner.scan_video()

        assert len(videos) == 1
        assert videos[0].normalized == "arcticanimals"

    def test_scan_with_level_filter(self, tmp_path):
        # Create both E and F level files
        e_dir = tmp_path / "RAZ-pdf点读版" / "E.PDF"
        f_dir = tmp_path / "RAZ-pdf点读版" / "F.PDF"
        e_dir.mkdir(parents=True)
        f_dir.mkdir(parents=True)
        (e_dir / "E Book.pdf").write_text("fake")
        (f_dir / "F Book.pdf").write_text("fake")

        scanner = ResourceScanner(tmp_path)
        e_pdfs = scanner.scan_pdfs(level="e")

        assert len(e_pdfs) == 1
        assert e_pdfs[0].level == "e"
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/test_scanner.py -v
```

Expected: All 6 tests pass

- [ ] **Step 4: Commit**

```bash
git add tools/raz_adapter/scanner.py tests/test_scanner.py
git commit -m "feat(scanner): add resource scanner for PDF/audio/video"
```

---

## Task 5: Resource Matcher

**Files:**
- Create: `tools/raz_adapter/matcher.py`

- [ ] **Step 1: Write the matcher**

Create `tools/raz_adapter/matcher.py`:

```python
"""Match resources (PDF, audio, video) by normalized book name."""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from .scanner import Resource


@dataclass
class MatchedBook:
    """A book with all matched resources."""

    normalized_name: str
    title: str
    level: str
    pdf: Optional[Resource]
    audio: Optional[Resource]
    video: Optional[Resource]


class ResourceMatcher:
    """Match audio, video, and PDF resources by normalized name."""

    def __init__(
        self,
        pdfs: list[Resource],
        audio: list[Resource],
        video: list[Resource],
    ):
        self.pdfs = {r.normalized: r for r in pdfs}
        self.audio = {r.normalized: r for r in audio}
        self.video = {r.normalized: r for r in video}

    def match_all(self) -> list[MatchedBook]:
        """
        Match all resources.

        Returns:
            List of matched books. Only includes books with at least
            audio (required) and pdf (required).
        """
        # Use audio as the base since every book must have audio
        all_keys = set(self.audio.keys())
        matched = []

        for key in all_keys:
            audio_res = self.audio.get(key)
            pdf_res = self.pdfs.get(key)

            if not audio_res:
                continue  # Audio is required

            if not pdf_res:
                print(f"Warning: No PDF found for '{key}', skipping")
                continue

            # Derive title from PDF name (usually cleaner)
            title = pdf_res.name if pdf_res else audio_res.name

            matched.append(MatchedBook(
                normalized_name=key,
                title=title,
                level=audio_res.level,
                pdf=pdf_res,
                audio=audio_res,
                video=self.video.get(key),
            ))

        return matched

    def get_unmatched(self) -> dict[str, list[Resource]]:
        """Get resources that couldn't be matched."""
        audio_keys = set(self.audio.keys())
        pdf_keys = set(self.pdfs.keys())
        video_keys = set(self.video.keys())

        all_keys = audio_keys | pdf_keys | video_keys
        matched_keys = audio_keys & pdf_keys  # Need both audio and PDF

        unmatched = {
            "audio": [],
            "pdf": [],
            "video": [],
        }

        for key in audio_keys - matched_keys:
            unmatched["audio"].append(self.audio[key])
        for key in pdf_keys - matched_keys:
            unmatched["pdf"].append(self.pdfs[key])
        for key in video_keys - matched_keys:
            unmatched["video"].append(self.video[key])

        return unmatched
```

- [ ] **Step 2: Create tests**

Create `tests/test_matcher.py`:

```python
"""Tests for resource matcher."""

import pytest
from pathlib import Path
from raz_adapter.matcher import ResourceMatcher, MatchedBook
from raz_adapter.scanner import Resource


class TestResourceMatcher:
    def test_match_complete_book(self):
        pdf = Resource(
            path=Path("/pdf/Arctic Animals.pdf"),
            name="Arctic Animals",
            normalized="arcticanimals",
            level="e",
            resource_type="pdf",
        )
        audio = Resource(
            path=Path("/audio/01 arctic animals.mp3"),
            name="01 arctic animals",
            normalized="arcticanimals",
            level="e",
            resource_type="audio",
        )
        video = Resource(
            path=Path("/video/E-01Arctic Animals.mp4"),
            name="E-01Arctic Animals",
            normalized="arcticanimals",
            level="e",
            resource_type="video",
        )

        matcher = ResourceMatcher([pdf], [audio], [video])
        matches = matcher.match_all()

        assert len(matches) == 1
        assert matches[0].normalized_name == "arcticanimals"
        assert matches[0].title == "Arctic Animals"
        assert matches[0].pdf == pdf
        assert matches[0].audio == audio
        assert matches[0].video == video

    def test_match_without_video(self):
        pdf = Resource(
            path=Path("/pdf/Test.pdf"),
            name="Test",
            normalized="test",
            level="e",
            resource_type="pdf",
        )
        audio = Resource(
            path=Path("/audio/01 test.mp3"),
            name="01 test",
            normalized="test",
            level="e",
            resource_type="audio",
        )

        matcher = ResourceMatcher([pdf], [audio], [])
        matches = matcher.match_all()

        assert len(matches) == 1
        assert matches[0].video is None

    def test_skip_missing_pdf(self, capsys):
        audio = Resource(
            path=Path("/audio/01 test.mp3"),
            name="01 test",
            normalized="test",
            level="e",
            resource_type="audio",
        )

        matcher = ResourceMatcher([], [audio], [])
        matches = matcher.match_all()

        assert len(matches) == 0

    def test_get_unmatched(self):
        pdf = Resource(
            path=Path("/pdf/Only Pdf.pdf"),
            name="Only Pdf",
            normalized="onlypdf",
            level="e",
            resource_type="pdf",
        )
        audio = Resource(
            path=Path("/audio/01 only audio.mp3"),
            name="01 only audio",
            normalized="onlyaudio",
            level="e",
            resource_type="audio",
        )

        matcher = ResourceMatcher([pdf], [audio], [])
        unmatched = matcher.get_unmatched()

        assert len(unmatched["pdf"]) == 1
        assert len(unmatched["audio"]) == 1
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/test_matcher.py -v
```

Expected: All 4 tests pass

- [ ] **Step 4: Commit**

```bash
git add tools/raz_adapter/matcher.py tests/test_matcher.py
git commit -m "feat(matcher): add resource matching by normalized name"
```

---

## Task 6: Audio Transcriber

**Files:**
- Create: `tools/raz_adapter/transcriber.py`

- [ ] **Step 1: Write the transcriber**

Create `tools/raz_adapter/transcriber.py`:

```python
"""Audio transcription using faster-whisper."""

from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel

from .models import Sentence


class Transcriber:
    """Transcribe audio and generate sentence-level timestamps."""

    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
    ):
        self.model = WhisperModel(
            model_size, device=device, compute_type=compute_type
        )

    def transcribe(
        self,
        audio_path: Path | str,
        confidence_threshold: float = 0.8,
    ) -> list[Sentence]:
        """
        Transcribe audio file to sentences with timestamps.

        Args:
            audio_path: Path to audio file
            confidence_threshold: Minimum confidence for sentences

        Returns:
            List of Sentence objects with timing info
        """
        segments, info = self.model.transcribe(
            str(audio_path),
            language="en",
            word_timestamps=True,
            vad_filter=True,
        )

        sentences = []
        current_words = []
        current_text = []

        for segment in segments:
            if not segment.words:
                continue

            for word in segment.words:
                current_words.append(word)
                current_text.append(word.word)

                # Check for sentence boundary
                text = word.word.strip()
                if text.endswith((".", "?", "!")):
                    sentence = self._create_sentence(
                        current_words, current_text, confidence_threshold
                    )
                    if sentence:
                        sentences.append(sentence)
                    current_words = []
                    current_text = []

        # Handle any remaining words
        if current_words:
            sentence = self._create_sentence(
                current_words, current_text, confidence_threshold
            )
            if sentence:
                sentences.append(sentence)

        return sentences

    def _create_sentence(
        self,
        words: list,
        text_parts: list[str],
        confidence_threshold: float,
    ) -> Optional[Sentence]:
        """Create a Sentence from accumulated words."""
        if not words:
            return None

        # Skip if too short (< 0.3s)
        duration = words[-1].end - words[0].start
        if duration < 0.3:
            return None

        text = "".join(text_parts).strip()
        if not text:
            return None

        # Calculate average confidence
        confidences = [getattr(w, "probability", 1.0) for w in words]
        avg_confidence = sum(confidences) / len(confidences)

        return Sentence(
            start=round(words[0].start, 2),
            end=round(words[-1].end, 2),
            text=text,
            page=1,  # Will be updated by generator
            confidence=round(avg_confidence, 3),
        )
```

- [ ] **Step 2: Create tests**

Create `tests/test_transcriber.py`:

```python
"""Tests for transcriber."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from raz_adapter.transcriber import Transcriber
from raz_adapter.models import Sentence


class MockWord:
    def __init__(self, word, start, end, probability=0.95):
        self.word = word
        self.start = start
        self.end = end
        self.probability = probability


class MockSegment:
    def __init__(self, words):
        self.words = words


class TestTranscriber:
    @patch("raz_adapter.transcriber.WhisperModel")
    def test_transcribe_creates_sentences(self, mock_model_class):
        # Setup mock
        mock_model = Mock()
        mock_model_class.return_value = mock_model

        # Mock segments with words forming sentences
        words = [
            MockWord("Hello ", 0.0, 0.5),
            MockWord("world.", 0.5, 1.0),
            MockWord("How ", 1.5, 2.0),
            MockWord("are ", 2.0, 2.3),
            MockWord("you?", 2.3, 2.8),
        ]
        mock_segment = MockSegment(words)
        mock_model.transcribe.return_value = ([mock_segment], None)

        transcriber = Transcriber()
        sentences = transcriber.transcribe("fake.mp3")

        assert len(sentences) == 2
        assert sentences[0].text == "Hello world."
        assert sentences[0].start == 0.0
        assert sentences[0].end == 1.0
        assert sentences[1].text == "How are you?"

    @patch("raz_adapter.transcriber.WhisperModel")
    def test_skip_short_fragments(self, mock_model_class):
        mock_model = Mock()
        mock_model_class.return_value = mock_model

        # Very short words (< 0.3s total)
        words = [MockWord("Hi.", 0.0, 0.2)]
        mock_segment = MockSegment(words)
        mock_model.transcribe.return_value = ([mock_segment], None)

        transcriber = Transcriber()
        sentences = transcriber.transcribe("fake.mp3")

        assert len(sentences) == 0  # Too short, filtered out

    @patch("raz_adapter.transcriber.WhisperModel")
    def test_confidence_calculation(self, mock_model_class):
        mock_model = Mock()
        mock_model_class.return_value = mock_model

        words = [
            MockWord("Test ", 0.0, 0.5, 0.9),
            MockWord("sentence.", 0.5, 1.0, 0.8),
        ]
        mock_segment = MockSegment(words)
        mock_model.transcribe.return_value = ([mock_segment], None)

        transcriber = Transcriber()
        sentences = transcriber.transcribe("fake.mp3")

        assert len(sentences) == 1
        assert sentences[0].confidence == 0.85  # Average of 0.9 and 0.8
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/test_transcriber.py -v
```

Expected: All 3 tests pass

- [ ] **Step 4: Commit**

```bash
git add tools/raz_adapter/transcriber.py tests/test_transcriber.py
git commit -m "feat(transcriber): add Whisper ASR with sentence-level timestamps"
```

---

## Task 7: Book Generator

**Files:**
- Create: `tools/raz_adapter/generator.py`

- [ ] **Step 1: Write the generator**

Create `tools/raz_adapter/generator.py`:

```python
"""Generate book.json and copy resources."""

import shutil
import json
from pathlib import Path

from .models import Book, Sentence
from .matcher import MatchedBook
from .normalizer import to_kebab_case
from .transcriber import Transcriber


class BookGenerator:
    """Generate book.json and copy associated resources."""

    def __init__(
        self,
        output_dir: Path | str,
        transcriber: Transcriber,
        dry_run: bool = False,
        force: bool = False,
        backup: bool = False,
        confidence_threshold: float = 0.8,
    ):
        self.output_dir = Path(output_dir)
        self.transcriber = transcriber
        self.dry_run = dry_run
        self.force = force
        self.backup = backup
        self.confidence_threshold = confidence_threshold

    def generate(self, matched: MatchedBook) -> tuple[Book, list[str]]:
        """
        Generate book.json for a matched book.

        Returns:
            Tuple of (Book, warnings)
        """
        warnings = []

        # Create output directory
        book_dir = self.output_dir / f"level-{matched.level}" / to_kebab_case(matched.title)

        if not self.dry_run:
            book_dir.mkdir(parents=True, exist_ok=True)

        # Transcribe audio
        sentences = self.transcriber.transcribe(
            matched.audio.path, self.confidence_threshold
        )

        # Check for low confidence
        low_conf = [s for s in sentences if s.confidence < self.confidence_threshold]
        if low_conf:
            warnings.append(
                f"{len(low_conf)} sentences below confidence threshold"
            )

        # Create Book model
        book = Book(
            id=f"level-{matched.level}/{to_kebab_case(matched.title)}",
            title=matched.title,
            level=matched.level,
            sentences=sentences,
        )

        if not self.dry_run:
            # Check for existing
            json_path = book_dir / "book.json"
            if json_path.exists() and not self.force:
                raise FileExistsError(f"{json_path} exists. Use --force to overwrite")

            if json_path.exists() and self.backup:
                shutil.copy2(json_path, json_path.with_suffix(".json.bak"))

            # Copy resources
            if matched.pdf:
                shutil.copy2(matched.pdf.path, book_dir / "book.pdf")
            if matched.audio:
                shutil.copy2(matched.audio.path, book_dir / "audio.mp3")
            if matched.video:
                shutil.copy2(matched.video.path, book_dir / "video.mp4")

            # Save book.json
            book.save(json_path)

        return book, warnings

    def generate_batch(
        self, matched_books: list[MatchedBook]
    ) -> tuple[list[Book], list[tuple[str, str]]]:
        """
        Generate books in batch.

        Returns:
            Tuple of (successful_books, errors)
        """
        books = []
        errors = []

        for i, matched in enumerate(matched_books, 1):
            print(f"[{i}/{len(matched_books)}] Processing: {matched.title}")

            try:
                book, warnings = self.generate(matched)
                books.append(book)

                if warnings:
                    for w in warnings:
                        print(f"  Warning: {w}")

                print(f"  Done: {len(book.sentences)} sentences")

            except Exception as e:
                errors.append((matched.title, str(e)))
                print(f"  Error: {e}")

        return books, errors
```

- [ ] **Step 2: Create tests**

Create `tests/test_generator.py`:

```python
"""Tests for book generator."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from raz_adapter.generator import BookGenerator
from raz_adapter.matcher import MatchedBook
from raz_adapter.scanner import Resource
from raz_adapter.models import Sentence


class TestBookGenerator:
    @patch("raz_adapter.generator.Transcriber")
    @patch("shutil.copy2")
    def test_generate_copies_resources(self, mock_copy, mock_transcriber_class, tmp_path):
        # Setup
        mock_transcriber = Mock()
        mock_transcriber.transcribe.return_value = [
            Sentence(start=0, end=1, text="Test.", page=1, confidence=0.95)
        ]
        mock_transcriber_class.return_value = mock_transcriber

        matched = MatchedBook(
            normalized_name="testbook",
            title="Test Book",
            level="e",
            pdf=Resource(
                path=tmp_path / "test.pdf",
                name="Test Book",
                normalized="testbook",
                level="e",
                resource_type="pdf",
            ),
            audio=Resource(
                path=tmp_path / "test.mp3",
                name="01 test book",
                normalized="testbook",
                level="e",
                resource_type="audio",
            ),
            video=None,
        )

        # Create dummy files
        (tmp_path / "test.pdf").write_text("pdf")
        (tmp_path / "test.mp3").write_text("mp3")

        generator = BookGenerator(tmp_path / "output", mock_transcriber)
        book, warnings = generator.generate(matched)

        # Verify
        assert book.id == "level-e/test-book"
        assert book.title == "Test Book"
        assert len(book.sentences) == 1

        # Check files were copied
        output_dir = tmp_path / "output" / "level-e" / "test-book"
        assert (output_dir / "book.json").exists()

    @patch("raz_adapter.generator.Transcriber")
    def test_dry_run_does_not_copy(self, mock_transcriber_class, tmp_path):
        mock_transcriber = Mock()
        mock_transcriber.transcribe.return_value = []
        mock_transcriber_class.return_value = mock_transcriber

        matched = MatchedBook(
            normalized_name="test",
            title="Test",
            level="e",
            pdf=None,
            audio=Resource(
                path=tmp_path / "test.mp3",
                name="test",
                normalized="test",
                level="e",
                resource_type="audio",
            ),
            video=None,
        )

        generator = BookGenerator(tmp_path / "output", mock_transcriber, dry_run=True)
        book, _ = generator.generate(matched)

        # In dry-run, output dir should not be created
        assert not (tmp_path / "output").exists()

    @patch("raz_adapter.generator.Transcriber")
    def test_low_confidence_warning(self, mock_transcriber_class, tmp_path):
        mock_transcriber = Mock()
        mock_transcriber.transcribe.return_value = [
            Sentence(start=0, end=1, text="Test.", page=1, confidence=0.5)
        ]
        mock_transcriber_class.return_value = mock_transcriber

        matched = MatchedBook(
            normalized_name="test",
            title="Test",
            level="e",
            pdf=None,
            audio=Resource(
                path=tmp_path / "test.mp3",
                name="test",
                normalized="test",
                level="e",
                resource_type="audio",
            ),
            video=None,
        )

        generator = BookGenerator(
            tmp_path / "output",
            mock_transcriber,
            dry_run=True,
            confidence_threshold=0.8,
        )
        _, warnings = generator.generate(matched)

        assert len(warnings) == 1
        assert "confidence threshold" in warnings[0]
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/test_generator.py -v
```

Expected: All 3 tests pass

- [ ] **Step 4: Commit**

```bash
git add tools/raz_adapter/generator.py tests/test_generator.py
git commit -m "feat(generator): add book.json generation and resource copying"
```

---

## Task 8: CLI Interface

**Files:**
- Create: `tools/raz_adapter/cli.py`

- [ ] **Step 1: Write the CLI**

Create `tools/raz_adapter/cli.py`:

```python
"""Command-line interface for RAZ adapter."""

import sys
from pathlib import Path

import click
from tqdm import tqdm

from .scanner import ResourceScanner
from .matcher import ResourceMatcher
from .transcriber import Transcriber
from .generator import BookGenerator


@click.command()
@click.option(
    "--level",
    type=str,
    help="Process entire level (e.g., 'e', 'aa', 'z1')",
)
@click.option(
    "--resourcer-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default="raz-resourcer",
    help="Path to raz-resourcer directory",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True),
    default="data/raz",
    help="Output directory for processed books",
)
@click.option(
    "--model",
    type=click.Choice(["tiny", "base", "small", "medium", "large"]),
    default="small",
    help="Whisper model size",
)
@click.option(
    "--device",
    type=click.Choice(["cpu", "cuda"]),
    default="cpu",
    help="Inference device",
)
@click.option(
    "--workers",
    type=int,
    default=None,
    help="Number of parallel workers (default: CPU cores for CPU mode, 1 for GPU)",
)
@click.option(
    "--confidence-threshold",
    type=float,
    default=0.8,
    help="Confidence threshold for marking low-quality transcriptions",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview processing without generating files",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing book.json files",
)
@click.option(
    "--backup",
    is_flag=True,
    help="Create .bak backup before overwriting",
)
@click.option(
    "--on-duplicate",
    type=click.Choice(["skip", "replace", "error"]),
    default="error",
    help="Action when book.json already exists",
)
def main(
    level: str | None,
    resourcer_dir: str,
    output_dir: str,
    model: str,
    device: str,
    workers: int | None,
    confidence_threshold: float,
    dry_run: bool,
    force: bool,
    backup: bool,
    on_duplicate: str,
):
    """
    RAZ Resource Adapter - Convert resources to book.json format.

    Examples:
        # Process entire E level
        python -m tools.raz_adapter --level e

        # Process with tiny model for testing
        python -m tools.raz_adapter --level e --model tiny

        # Dry run to preview
        python -m tools.raz_adapter --level e --dry-run
    """
    resourcer_path = Path(resourcer_dir)
    output_path = Path(output_dir)

    if not level:
        click.echo("Error: --level is required", err=True)
        sys.exit(1)

    click.echo(f"Processing level '{level.upper()}'...")
    click.echo(f"Model: {model}, Device: {device}")
    if dry_run:
        click.echo("DRY RUN - No files will be created")

    # Scan resources
    click.echo("\nScanning resources...")
    scanner = ResourceScanner(resourcer_path)
    pdfs, audio, video = scanner.scan_all(level=level)

    click.echo(f"  Found: {len(pdfs)} PDFs, {len(audio)} audio, {len(video)} videos")

    # Match resources
    matcher = ResourceMatcher(pdfs, audio, video)
    matched = matcher.match_all()
    unmatched = matcher.get_unmatched()

    click.echo(f"\nMatched: {len(matched)} books")

    if unmatched["pdf"]:
        click.echo(f"  Warning: {len(unmatched['pdf'])} unmatched PDFs")
    if unmatched["audio"]:
        click.echo(f"  Warning: {len(unmatched['audio'])} unmatched audio files")
    if unmatched["video"]:
        click.echo(f"  Warning: {len(unmatched['video'])} unmatched videos")

    if not matched:
        click.echo("No books to process. Exiting.")
        sys.exit(0)

    # Initialize transcriber
    click.echo(f"\nLoading Whisper model '{model}'...")
    transcriber = Transcriber(model_size=model, device=device)

    # Generate books
    generator = BookGenerator(
        output_path,
        transcriber,
        dry_run=dry_run,
        force=force,
        backup=backup,
        confidence_threshold=confidence_threshold,
    )

    click.echo(f"\nProcessing {len(matched)} books...\n")
    books, errors = generator.generate_batch(matched)

    # Summary
    click.echo(f"\n{'=' * 50}")
    click.echo(f"Completed: {len(books)} books")
    click.echo(f"Errors: {len(errors)}")

    if errors:
        click.echo("\nErrors:")
        for title, error in errors:
            click.echo(f"  - {title}: {error}")

    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Create __main__.py**

Create `tools/raz_adapter/__main__.py`:

```python
"""Entry point for python -m tools.raz_adapter."""

from .cli import main

main()
```

- [ ] **Step 3: Test CLI help**

```bash
cd tools && python -m raz_adapter --help
```

Expected: Help text displays with all options

- [ ] **Step 4: Update package exports**

Update `tools/raz_adapter/__init__.py`:

```python
"""RAZ Resource Adapter - Convert resources to book.json format."""

__version__ = "1.0.0"

from .models import Book, Sentence
from .normalizer import normalize_name, to_kebab_case
from .matcher import ResourceMatcher
from .transcriber import Transcriber
from .generator import BookGenerator

__all__ = [
    "Book",
    "Sentence",
    "normalize_name",
    "to_kebab_case",
    "ResourceMatcher",
    "Transcriber",
    "BookGenerator",
]
```

- [ ] **Step 5: Commit**

```bash
git add tools/raz_adapter/cli.py tools/raz_adapter/__main__.py tools/raz_adapter/__init__.py
git commit -m "feat(cli): add Click CLI with full option support"
```

---

## Task 9: Integration Testing

**Files:**
- Create: `tests/test_integration.py`
- Create: `tests/fixtures/README.md`

- [ ] **Step 1: Create integration test**

Create `tests/test_integration.py`:

```python
"""Integration tests for full pipeline."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from raz_adapter.scanner import ResourceScanner
from raz_adapter.matcher import ResourceMatcher
from raz_adapter.generator import BookGenerator
from raz_adapter.transcriber import Transcriber
from raz_adapter.models import Sentence


class TestFullPipeline:
    def test_end_to_end_single_book(self, tmp_path):
        """Test complete pipeline with mocked transcriber."""
        # Setup test resources
        resourcer = tmp_path / "raz-resourcer"
        output = tmp_path / "output"

        # Create PDF
        pdf_dir = resourcer / "RAZ-pdf点读版" / "E.PDF"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "Arctic Animals.pdf").write_text("PDF content")

        # Create audio
        audio_dir = resourcer / "RAZ AA级-Z音频" / "E级音频"
        audio_dir.mkdir(parents=True)
        (audio_dir / "01 arctic animals.mp3").write_text("MP3 content")

        # Scan
        scanner = ResourceScanner(resourcer)
        pdfs, audio, video = scanner.scan_all(level="e")

        assert len(pdfs) == 1
        assert len(audio) == 1

        # Match
        matcher = ResourceMatcher(pdfs, audio, [])
        matched = matcher.match_all()

        assert len(matched) == 1
        assert matched[0].normalized_name == "arcticanimals"

        # Mock transcriber
        mock_transcriber = Mock(spec=Transcriber)
        mock_transcriber.transcribe.return_value = [
            Sentence(start=0.0, end=3.2, text="Arctic Animals.", page=1, confidence=0.95)
        ]

        # Generate
        generator = BookGenerator(output, mock_transcriber)
        books, errors = generator.generate_batch(matched)

        assert len(books) == 1
        assert len(errors) == 0

        # Verify output
        book_dir = output / "level-e" / "arctic-animals"
        assert (book_dir / "book.json").exists()
        assert (book_dir / "book.pdf").exists()
        assert (book_dir / "audio.mp3").exists()

        # Verify JSON structure
        with open(book_dir / "book.json") as f:
            data = json.load(f)

        assert data["id"] == "level-e/arctic-animals"
        assert data["title"] == "Arctic Animals"
        assert data["level"] == "e"
        assert data["pdf"] == "book.pdf"
        assert data["audio"] == "audio.mp3"
        assert data["video"] is None
        assert len(data["sentences"]) == 1
        assert data["sentences"][0]["text"] == "Arctic Animals."
```

- [ ] **Step 2: Create fixtures README**

Create `tests/fixtures/README.md`:

```markdown
# Test Fixtures

This directory contains test files for integration tests.

## Files Needed

- `sample.mp3` - 30 second test audio (can use any short audio file)
- `sample.pdf` - 3 page test PDF (can use any small PDF)

## Generating Fixtures

For actual testing, you can use:
- Audio: Any short MP3 file from public domain sources
- PDF: Empty 3-page PDF created with any PDF tool

Note: These are not included in git due to size. Tests mock the transcriber
to avoid needing actual Whisper models during CI.
```

- [ ] **Step 3: Run integration tests**

```bash
python -m pytest tests/test_integration.py -v
```

Expected: Integration test passes

- [ ] **Step 4: Run all tests**

```bash
python -m pytest tests/ -v --tb=short
```

Expected: All 30+ tests pass

- [ ] **Step 5: Commit**

```bash
git add tests/test_integration.py tests/fixtures/
git commit -m "test(integration): add end-to-end pipeline test"
```

---

## Task 10: Documentation

**Files:**
- Create: `tools/README.md`

- [ ] **Step 1: Write README**

Create `tools/README.md`:

```markdown
# RAZ Resource Adapter

Convert RAZ learning resources to the new book.json format with sentence-level
timestamps.

## Installation

```bash
cd tools
pip install -r requirements.txt
```

Requires Python 3.10+, ffmpeg, and ~500MB disk space for Whisper models.

## Usage

### Process a Single Level

```bash
cd tools && python -m raz_adapter --level e
```

This will:
1. Scan `../raz-resourcer/` for E-level resources
2. Match PDF/audio/video by book name
3. Transcribe audio with Whisper
4. Generate `book.json` and copy assets to `../data/raz/level-e/`

### Options

| Option | Description |
|--------|-------------|
| `--level` | Level to process (e.g., 'e', 'aa', 'z1') |
| `--model` | Whisper model: tiny, base, small, medium, large |
| `--device` | cpu or cuda |
| `--dry-run` | Preview without generating files |
| `--force` | Overwrite existing files |
| `--confidence-threshold` | Mark low-confidence sentences (default 0.8) |

### Testing

```bash
pytest tests/ -v
```

## Output Format

```json
{
  "id": "level-e/arctic-animals",
  "title": "Arctic Animals",
  "level": "e",
  "pdf": "book.pdf",
  "video": "video.mp4",
  "audio": "audio.mp3",
  "sentences": [
    {
      "start": 0.5,
      "end": 3.2,
      "text": "Arctic Animals.",
      "page": 1,
      "confidence": 0.95
    }
  ]
}
```
```

- [ ] **Step 2: Commit**

```bash
git add tools/README.md
git commit -m "docs: add README with usage instructions"
```

---

## Summary

This implementation creates a complete RAZ Resource Adapter with:

1. **Models** - Pydantic schemas for book.json
2. **Normalizer** - Book name matching across file types
3. **Scanner** - Discovers PDF/audio/video resources
4. **Matcher** - Links resources by normalized name
5. **Transcriber** - Whisper ASR with sentence timestamps
6. **Generator** - Creates book.json and copies assets
7. **CLI** - Full command-line interface
8. **Tests** - Comprehensive unit and integration tests

Total: 10 tasks, ~30 test cases

Run with:
```bash
cd tools && python -m raz_adapter --level e --model small
```
