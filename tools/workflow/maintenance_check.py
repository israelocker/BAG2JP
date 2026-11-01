#!/usr/bin/env python3
"""Run all maintenance checks in sequence.

Usage:
    py tools/workflow/maintenance_check.py [--fix]

Runs:
    1. validate_frontmatter.py
    2. generate_digests.py --check-only
    3. measure_context.py

Exit code: 0 if all checks pass, 1 if any issue found.
"""

import logging
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = ROOT / "tools" / "workflow"

logger = logging.getLogger("maintenance_check")


def run(script: str, args: list[str] | None = None) -> int:
    """Run a maintenance script and return its exit code."""
    cmd = [sys.executable, str(TOOLS_DIR / script)]
    if args:
        cmd.extend(args)
    print(f"\n{'=' * 60}")
    logger.info(f"Running: {script} {' '.join(args or [])}")
    print(f"{'=' * 60}")
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


def main() -> int:
    fix = "--fix" in sys.argv
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    exit_code = 0

    # 1. Validate frontmatter
    rc = run("validate_frontmatter.py", ["--fix"] if fix else None)
    if rc != 0:
        exit_code = 1

    # 2. Check digests are fresh
    rc = run("generate_digests.py", ["--check-only"])
    if rc != 0:
        logger.warning("  -> Run: py tools/workflow/generate_digests.py --all")
        exit_code = 1

    # 3. Measure context size
    rc = run("measure_context.py", ["--detailed"])
    if rc != 0:
        exit_code = 1

    print(f"\n{'=' * 60}")
    if exit_code == 0:
        logger.info("ALL MAINTENANCE CHECKS PASSED [OK]")
    else:
        logger.warning("MAINTENANCE ISSUES FOUND [WARN]")
    print(f"{'=' * 60}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())