#!/usr/bin/env python3
"""Validate that all notes/*.md files have required frontmatter fields.

Usage:
    py tools/workflow/validate_frontmatter.py [--fix]

Required fields: id, title, tags, summary, related, created, updated
"""

import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
NOTES_DIR = ROOT / "notes"

REQUIRED_FIELDS = ["id", "title", "tags", "summary", "related", "created", "updated"]

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?)?$")

logger = logging.getLogger("validate_frontmatter")


def parse_frontmatter(content: str) -> Optional[dict]:
    """Return frontmatter dict if present, else None."""
    if not content.startswith("---\n"):
        return None
    end = content.find("\n---\n", 4)
    if end == -1:
        return None
    fm_block = content[4:end]
    fm: dict = {}
    for line in fm_block.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"')
    return fm


def validate_file(path: Path, fix: bool = False) -> list[str]:
    """Validate a single note file. Return list of issues."""
    issues: list[str] = []
    content = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(content)

    if fm is None:
        issues.append(f"MISSING frontmatter in {path.name}")
        if fix:
            now = datetime.now().strftime("%Y-%m-%d")
            title = path.stem.replace("-", " ").title()
            new_fm = (
                f"---\n"
                f"id: {path.stem}\n"
                f"title: \"{title}\"\n"
                f"tags: []\n"
                f"summary: \"Auto-generated frontmatter - please review\"\n"
                f"related: []\n"
                f"created: {now}\n"
                f"updated: {now}\n"
                f"---\n"
            )
            path.write_text(new_fm + content, encoding="utf-8")
            issues.append(f"  -> Added minimal frontmatter to {path.name}")
        return issues

    for field in REQUIRED_FIELDS:
        if field not in fm or not fm[field]:
            issues.append(f"MISSING field '{field}' in {path.name}")
            if fix:
                now = datetime.now().strftime("%Y-%m-%d")
                defaults = {
                    "id": path.stem,
                    "title": path.stem.replace("-", " ").title(),
                    "tags": "[]",
                    "summary": "",
                    "related": "[]",
                    "created": now,
                    "updated": now,
                }
                fm[field] = defaults.get(field, "")
                issues.append(f"  -> Filled '{field}' in {path.name}")

    if "updated" in fm and not DATE_PATTERN.match(fm["updated"]):
        issues.append(f"INVALID date format for 'updated' in {path.name}: {fm['updated']}")

    return issues


def main() -> int:
    fix = "--fix" in sys.argv
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    md_files = sorted(NOTES_DIR.glob("*.md"))

    if not md_files:
        logger.warning("No markdown files found in notes/")
        return 1

    total_issues = 0
    for f in md_files:
        issues = validate_file(f, fix=fix)
        if issues:
            for issue in issues:
                logger.warning(issue)
            total_issues += len(issues)

    if total_issues == 0:
        logger.info(f"All {len(md_files)} notes have valid frontmatter.")
    else:
        action = "fixed" if fix else "found"
        logger.warning(f"{total_issues} issue(s) {action} across {len(md_files)} notes.")
        if not fix:
            logger.info("Run with --fix to auto-fill missing fields.")

    return 1 if total_issues and not fix else 0


if __name__ == "__main__":
    raise SystemExit(main())