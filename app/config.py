from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = BASE_DIR / "data"
CHARACTERS_DIR = DATA_DIR / "characters"
RECORDS_DIR = DATA_DIR / "records"

CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
RECORDS_DIR.mkdir(parents=True, exist_ok=True)
