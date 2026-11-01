#!/usr/bin/env python3
"""Generate/update digests for large source files.

Usage:
    py tools/workflow/generate_digests.py [--all] [--check-only] [--file <path>]

The script reads source files and produces a digest markdown file in notes/digests/
containing only the essential sections (headings, key decisions, references).
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIGESTS_DIR = ROOT / "notes" / "digests"

# Mapping: source_file -> digest_file
SOURCE_TO_DIGEST = {
    "CHARACTER_IMPORT.md": "character_import.digest.md",
    "notes/bag1-character.md": "bag1-character.digest.md",
    "notes/bag1-stage-song.md": "bag1-stage-song.digest.md",
    "notes/online.md": "online.digest.md",
    "notes/project.md": "project.digest.md",
    "tools/bag1import/character_workflow.py": "character_workflow.digest.md",
}

# Sections to skip (test details, personal paths, debug output)
SKIP_PATTERNS = [
    r"D:\\\\Dev\\\\Tools",
    r"C:\\\\Users\\\\israe",
    r"D:\\\\Games",
    r"BAG2JP-exp-8mb",
    r"BAG2JP-win",
    r"_work/outputs",
    r"_work/shots",
    r"frame",
    r"f\d+",
    r"screenshot",
    r"capture",
    r"DEBUG",
    r"debug",
    r"test driver",
    r"test switch",
    r"probe",
    r"PSX_RB_PAD_TRACE",
    r"BAG2JP_WATCH",
    r"BAG2JP_AUDIO_DUMP",
    r"BAG2JP_AUDIO_PROBE",
    r"BAG2JP_NETSYNC",
    r"BAG2JP_TEST_DANCE_VIEW",
    r"winshot",
    r"postkey",
    r"sendkey",
    r"focus\.ps1",
    r"bag2_two\.ps1",
    r"bag2_1p\.ps1",
    r"bag2_setup_test",
    r"bag2_uninstall_test",
    r"check_shortcuts",
    r"realclick",
    r"typetext",
    r"postclick",
    r"keys_shot",
    r"np_cli",
    r"dbg\.ps1",
]


def should_skip_line(line: str) -> bool:
    """Return True if a line contains test/debug/personal-path noise."""
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def digest_exists_and_fresh(source: Path, digest: Path) -> bool:
    """Return True if digest exists and is newer than source."""
    if not digest.exists():
        return False
    return digest.stat().st_mtime >= source.stat().st_mtime


def extract_headings(content: str) -> list[str]:
    """Extract markdown headings from content."""
    headings = []
    for line in content.splitlines():
        if re.match(r"^#{1,6}\s", line):
            headings.append(line.strip())
    return headings


def extract_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter if present."""
    if not content.startswith("---\n"):
        return {}
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}
    fm_block = content[4:end]
    fm = {}
    for line in fm_block.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"')
    return fm


def generate_digest(source: Path, digest: Path) -> str:
    """Generate a digest markdown file from a source file."""
    content = source.read_text(encoding="utf-8")
    fm = extract_frontmatter(content)
    headings = extract_headings(content)

    # Filter out test/debug lines
    clean_lines = []
    for line in content.splitlines():
        if not should_skip_line(line):
            clean_lines.append(line)
    clean_content = "\n".join(clean_lines)

    # Build digest
    lines = [
        f"# {source.stem.title()} Digest",
        "",
        f"**Source:** `{source.relative_to(ROOT)}` ({source.stat().st_size / 1024:.1f} KB)",
        f"**Generated:** {__import__('datetime').datetime.now().isoformat()}T00:00:00Z",
        "",
    ]

    if fm:
        lines.append("## Metadata")
        lines.append("")
        for key in ("id", "title", "tags", "summary", "related", "created", "updated"):
            if key in fm:
                lines.append(f"- **{key}:** {fm[key]}")
        lines.append("")

    if headings:
        lines.append("## Sections")
        lines.append("")
        for h in headings:
            lines.append(f"- {h}")
        lines.append("")

    lines.append("## Quick Reference")
    lines.append("")
    lines.append(f"Use this digest instead of reading `{source.name}` directly.")
    lines.append("")
    lines.append("Read the full source only when:")
    lines.append("- The digest doesn't answer your question")
    lines.append("- You need historical evidence details")
    lines.append("- You're doing a code review or audit")

    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return digest.name


def main():
    parser = argparse.ArgumentParser(description="Generate/update digests")
    parser.add_argument("--all", action="store_true", help="Regenerate all digests")
    parser.add_argument("--check-only", action="store_true", help="Only check if digests are stale")
    parser.add_argument("--file", type=Path, help="Specific source file to digest")
    args = parser.parse_args()

    targets = []
    if args.file:
        targets.append((args.file, DIGESTS_DIR / SOURCE_TO_DIGEST.get(args.file.name, args.file.stem + ".digest.md")))
    elif args.all or args.check_only:
        for src_name, digest_name in SOURCE_TO_DIGEST.items():
            src = ROOT / src_name
            dig = DIGESTS_DIR / digest_name
            if src.exists():
                targets.append((src, dig))

    if not targets:
        print("No targets specified. Use --all, --check-only, or --file <path>.")
        return 1

    stale = 0
    for src, dig in targets:
        if args.check_only:
            if not digest_exists_and_fresh(src, dig):
                print(f"STALE: {dig.name} (source: {src.name})")
                stale += 1
            else:
                print(f"OK: {dig.name}")
        else:
            name = generate_digest(src, dig)
            print(f"Generated: {name}")

    if args.check_only and stale:
        print(f"\n{stale} digest(es) need regeneration. Run: py tools/workflow/generate_digests.py --all")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())