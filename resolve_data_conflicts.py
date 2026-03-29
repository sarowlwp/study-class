#!/usr/bin/env python3
import subprocess
import sys

# Get list of unmerged files
result = subprocess.run(['git', 'ls-files', '-u'], capture_output=True, text=True)
unmerged_files = set()

for line in result.stdout.splitlines():
    parts = line.split('\t')
    if len(parts) >= 2:
        unmerged_files.add(parts[1])

# Checkout HEAD version for data files
data_prefixes = [
    'data/',
    'scripts/raz_sync_processor/',
]

for file_path in unmerged_files:
    if any(file_path.startswith(prefix) for prefix in data_prefixes):
        print(f"Checking out HEAD version: {file_path}")
        subprocess.run(['git', 'checkout', 'HEAD', '--', file_path], check=False)
    else:
        print(f"Keeping conflict for: {file_path}")

print("\nDone!")
