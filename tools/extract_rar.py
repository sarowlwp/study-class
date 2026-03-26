#!/usr/bin/env python3
"""Extract all rar files in raz-resourcer directory."""

import os
import rarfile
from pathlib import Path
from typing import Tuple


def extract_rar_files(base_dir: str) -> Tuple[int, int]:
    """Extract all rar files in the base directory."""
    base = Path(base_dir)
    extracted = 0
    failed = 0

    for rar_path in base.rglob("*.rar"):
        print(f"\nExtracting: {rar_path}")
        try:
            # Extract to the same directory as the rar file
            extract_dir = rar_path.parent

            with rarfile.RarFile(rar_path) as rf:
                rf.extractall(path=extract_dir)

            print(f"  -> Extracted to: {extract_dir}")
            extracted += 1

            # Remove the rar file after successful extraction
            os.remove(rar_path)
            print(f"  -> Removed: {rar_path.name}")

        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1

    return extracted, failed


def main():
    base_dir = "/Users/sarowlwp/Document/go/study-class/raz-resourcer"

    print("=" * 60)
    print("Extracting RAR files")
    print("=" * 60)

    extracted, failed = extract_rar_files(base_dir)

    print("\n" + "=" * 60)
    print(f"Extracted: {extracted}")
    print(f"Failed: {failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()
