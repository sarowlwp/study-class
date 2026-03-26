"""Resource scanner for discovering PDF, audio, and video files."""

import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

from .normalizer import normalize_name


@dataclass
class Resource:
    """A discovered resource file."""

    path: Path
    name: str
    normalized: str
    level: str
    resource_type: str  # "pdf", "audio", "video"
    # Optional mapping key for levels with different naming schemes (e.g., O level)
    match_key: Optional[str] = None


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
        "Z1": "z1",
        "Z2": "z2",
    }

    def __init__(self, resourcer_dir: Path):
        self.resourcer_dir = Path(resourcer_dir)

    def _extract_level(self, dirname: str) -> str:
        """Extract level code from directory name like 'E级音频' -> 'e'."""
        # Try to match level pattern: AA, A-Z, Z1, Z2
        match = re.match(r"^([A-Z]{1,2}\d?)", dirname)
        if match:
            level_key = match.group(1)
            return self.LEVEL_MAP.get(level_key, level_key.lower())
        return "unknown"

    def scan_level(self, level: str) -> List[Resource]:
        """Scan all resources for a specific level."""
        resources = []

        # Scan PDF directory
        pdf_dir = self._find_pdf_dir(level)
        if pdf_dir:
            resources.extend(self._scan_pdf_directory(pdf_dir, level))

        # Scan audio directory
        audio_dir = self._find_audio_dir(level)
        if audio_dir:
            resources.extend(self._scan_audio_directory(audio_dir, level))

        # Scan video directory
        video_dir = self._find_video_dir(level)
        if video_dir:
            resources.extend(self._scan_video_directory(video_dir, level))

        return resources

    def _find_pdf_dir(self, level: str) -> Optional[Path]:
        """Find PDF directory for level."""
        level_upper = level.upper()
        pdf_base = self.resourcer_dir / "RAZ-pdf点读版"
        if not pdf_base.exists():
            return None

        # Look for A.PDF, AA.PDF, E.PDF, etc. - exact match for level
        for item in pdf_base.iterdir():
            if item.is_dir():
                # Check for exact match: name should be like "A.PDF" or "AA.PDF"
                if item.name.upper() == f"{level_upper}.PDF":
                    return item
                # Special case: H.PF (typo in directory name)
                if level_upper == "H" and item.name.upper() == "H.PF":
                    return item
        return None

    def _find_audio_dir(self, level: str) -> Optional[Path]:
        """Find audio directory for level."""
        audio_base = self.resourcer_dir / "RAZ AA级-Z音频"
        if not audio_base.exists():
            return None

        level_name = level.upper()

        # First try: look for "X级音频" format
        for item in audio_base.iterdir():
            if item.is_dir() and "音频" in item.name:
                match = re.match(r"^([A-Z]{1,2}\d?)", item.name)
                if match and match.group(1) == level_name:
                    return item

        # Second try: look for "X级" format (U, Y levels)
        for item in audio_base.iterdir():
            if item.is_dir():
                match = re.match(r"^([A-Z]{1,2}\d?)级$", item.name)
                if match and match.group(1) == level_name:
                    return item

        return None

    def _find_video_dir(self, level: str) -> Optional[Path]:
        """Find video directory for level."""
        video_base = self.resourcer_dir / "RAZ视频"
        if not video_base.exists():
            return None

        # Look for "E级视频", etc. - exact level match
        level_name = level.upper()
        for item in video_base.iterdir():
            if item.is_dir() and "视频" in item.name:
                match = re.match(r"^([A-Z]{1,2}\d?)", item.name)
                if match and match.group(1) == level_name:
                    return item
        return None

    def _scan_pdf_directory(self, directory: Path, level: str) -> List[Resource]:
        """Scan PDF directory for PDF files."""
        resources = []
        for pdf_file in directory.glob("*.pdf"):
            name = pdf_file.stem  # filename without extension
            normalized = normalize_name(name)

            # For O level, extract special match key for cross-resource matching
            match_key = None
            if level == "o":
                match_key = self._extract_o_level_match_key(name)

            resources.append(
                Resource(
                    path=pdf_file,
                    name=name,
                    normalized=normalized,
                    level=level,
                    resource_type="pdf",
                    match_key=match_key,
                )
            )
        return resources

    def _extract_o_level_match_key(self, pdf_name: str) -> Optional[str]:
        """Extract match key from O level PDF name like 'raz_lo02_whales_clr'."""
        # Handle special case: raz_bmqlo_01_f
        if pdf_name.startswith("raz_bmqlo_"):
            return "1849thecaliforniagoldrush"

        # Extract code from raz_loXX_code_clr pattern
        match = re.match(r"^raz_[a-z]+\d+_([a-z_]+)_clr$", pdf_name)
        if match:
            code = match.group(1)
            # Map common codes to expected audio titles (normalized)
            code_mapping = {
                "whales": "whales",
                "jennyyoga": "jennylovesyoga",
                "makusani": "makusanislesson",
                "irmas": "irmassandwichshop",
                "spidermonkey": "spidermonkeysquestion",
                "olymlegends": "summerolympicslegends",
                "magicmigration": "themagicofmigration",
                "anansiwtrmelon": "anansiandthetalkingwatermelon",
                "katiesforest": "katiesforestfinds",
                "listangram": "listangramanimals",
                "shadowpeople": "theshadowpeople",
                "adogstale": "adogstale",
                "pepperking": "pepperthekingofspices",
                "saltrocks": "saltrocks",
                "yourejellyfish": "youreajellyfish",
                "chocolate": "allaboutchocolate",
                "johnnyappleseedheadswest": "johnnyappleseedheadswest",
                "meetingfatherinplymouth": "meetingfatherinplymouth",
                "rainydaysavings": "rainydaysavings",
                "balticrescue": "balticrescue",
                "barackobama": "barackobama",
                "bats": "bats",
                "littleredssecretsauce": "littleredssecretsauce",
                "mysteriousmars": "mysteriousmars",
                "paulbunyanandbabeblueox": "paulbunyanandbabetheblueox",
                "pecosbillridestornado": "pecosbillridesatornado",
                "plutosnewfriends": "plutosnewfriends",
                "sallyride": "sallyride",
                "troikacaninesuperhero": "troikacaninesuperhero",
                "wondersofnature": "wondersofnature",
                "annieoakley": "annieoakley",
                "backpacktax": "thebackpacktax",
                "beekeeper": "thebeekeeper",
                "georgewashingtoncarver": "georgewashingtoncarver",
                "heroratsratswhosavelives": "heroratsratswhosavelives",
                "janegoodall": "janegoodall",
                "lookingbigfoot": "lookingforbigfoot",
                "savinglastwildtigers": "savingthelastwildtigers",
                "scottysspringtraining": "scottysspringtraining",
                "threelittlepigswolfsstory": "threelittlepigsthewolfsstory",
                "woodsofwonder": "woodsofwonder",
            }
            return code_mapping.get(code)

        return None

    def _scan_audio_directory(self, directory: Path, level: str) -> List[Resource]:
        """Scan audio directory for MP3 files."""
        resources = []
        for audio_file in directory.glob("*.mp3"):
            name = audio_file.stem
            resources.append(
                Resource(
                    path=audio_file,
                    name=name,
                    normalized=normalize_name(name),
                    level=level,
                    resource_type="audio",
                )
            )
        return resources

    def _scan_video_directory(self, directory: Path, level: str) -> List[Resource]:
        """Scan video directory for MP4 files."""
        resources = []
        for video_file in directory.glob("*.mp4"):
            name = video_file.stem
            resources.append(
                Resource(
                    path=video_file,
                    name=name,
                    normalized=normalize_name(name),
                    level=level,
                    resource_type="video",
                )
            )
        return resources
