#!/usr/bin/env python3
"""Measure the context size a new chat would load on startup.

Usage:
    py tools/workflow/measure_context.py [--detailed]

Shows the total KB of essential startup files vs. full notes directory.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Minimal startup files (optimized protocol)
MINIMAL_FILES = [
    "AGENTS.md",
    "NOTES.md",
    "_work/current-state.json",
    "IMPORT_STANDARD.md",
]

# All notes directory files (old approach)
NOTES_DIR = ROOT / "notes"

# Digest files (alternative to full notes)
DIGESTS_DIR = ROOT / "notes" / "digests"


def size_kb(path: Path) -> float:
    if path.exists():
        return path.stat().st_size / 1024
    return 0.0


def main():
    detailed = "--detailed" in __import__("sys").argv

    print("=== Context Size Measurement ===\n")

    # Minimal startup
    minimal_total = 0.0
    print("Minimal startup files (new chat reads these first):")
    for f in MINIMAL_FILES:
        path = ROOT / f
        sz = size_kb(path)
        minimal_total += sz
        marker = "[OK]" if path.exists() else "[MISSING]"
        print(f"  {marker} {f}: {sz:.1f} KB")

    print(f"\n  TOTAL minimal: {minimal_total:.1f} KB")

    # Full notes directory
    notes_total = 0.0
    note_count = 0
    print("\nAll notes/ files (old approach - loads everything):")
    if NOTES_DIR.exists():
        for f in sorted(NOTES_DIR.glob("*.md")):
            sz = size_kb(f)
            notes_total += sz
            note_count += 1
            if detailed:
                print(f"   [FILE] {f.name}: {sz:.1f} KB")
        print(f"  TOTAL notes/ ({note_count} files): {notes_total:.1f} KB")

    # Digest alternative
    digest_total = 0.0
    digest_count = 0
    print("\nDigest files (alternative to reading full notes):")
    if DIGESTS_DIR.exists():
        for f in sorted(DIGESTS_DIR.glob("*.md")):
            sz = size_kb(f)
            digest_total += sz
            digest_count += 1
            if detailed:
                print(f"   [FILE] {f.name}: {sz:.1f} KB")
        print(f"  TOTAL digests ({digest_count} files): {digest_total:.1f} KB")

    # Summary
    print("\n=== Summary ===")
    print(f"Minimal startup:   {minimal_total:.1f} KB")
    if notes_total > 0:
        reduction = (1 - minimal_total / notes_total) * 100
        print(f"Full notes/:      {notes_total:.1f} KB  ({reduction:.0f}% reduction)")
    if minimal_total < 8:
        print("[OK] Goal achieved: minimal context under 8 KB")
    else:
        print("[WARN] Warning: minimal context over 8 KB goal")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())