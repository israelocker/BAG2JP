#!/usr/bin/env python3
"""Validate TOML configuration files for BAG2JP.

Checks that values fall within expected ranges and required fields exist.

Usage:
    py tools/workflow/validate_toml_config.py [--fix]

Currently validates:
    patches/BAG2JP-game.toml - [audio] buffer_ms, [video] settings
    installer/settings.toml  - [video], [controller] values
"""

import logging
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

logger = logging.getLogger("validate_toml_config")

# Validation rules: (file, section, key, min, max, required, expected_type)
# expected_type: "numeric" (default) or "string"
RULES: list[tuple[str, str, str, Optional[float], Optional[float], bool, str]] = [
    ("patches/BAG2JP-game.toml", "audio", "buffer_ms", 30.0, 500.0, True, "numeric"),
    ("patches/BAG2JP-game.toml", "video", "internal_resolution", None, None, False, "string"),
    ("patches/BAG2JP-game.toml", "video", "anisotropic_filtering", 1.0, 16.0, False, "numeric"),
    ("installer/settings.toml", "video", "window_width", 640.0, 7680.0, False, "numeric"),
    ("installer/settings.toml", "controller", "p1_deadzone", 0.0, 32767.0, False, "numeric"),
    ("installer/settings.toml", "controller", "p2_deadzone", 0.0, 32767.0, False, "numeric"),
]


def load_toml(path: Path) -> dict:
    """Load and parse a TOML file."""
    with path.open("rb") as f:
        return tomllib.load(f)


def validate() -> int:
    """Validate all configured TOML rules. Return number of issues."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    issues = 0
    for file_rel, section, key, vmin, vmax, required, expected_type in RULES:
        path = ROOT / file_rel
        if not path.exists():
            if required:
                logger.error(f"MISSING config file: {path}")
                issues += 1
            continue

        try:
            data = load_toml(path)
        except Exception as exc:
            logger.error(f"FAILED to parse {path}: {exc}")
            issues += 1
            continue

        section_data = data.get(section, {})
        if key not in section_data:
            if required:
                logger.error(f"MISSING [{section}] {key} in {path.name}")
                issues += 1
            continue

        value = section_data[key]
        if expected_type == "numeric":
            if not isinstance(value, (int, float)):
                logger.warning(
                    f"[{section}] {key} in {path.name} is not numeric: {value!r}"
                )
                issues += 1
                continue
            if vmin is not None and value < vmin:
                logger.warning(
                    f"[{section}] {key}={value} below minimum {vmin} in {path.name}"
                )
                issues += 1
            if vmax is not None and value > vmax:
                logger.warning(
                    f"[{section}] {key}={value} above maximum {vmax} in {path.name}"
                )
                issues += 1
        elif expected_type == "string":
            if not isinstance(value, str):
                logger.warning(
                    f"[{section}] {key} in {path.name} is not a string: {value!r}"
                )
                issues += 1

    if issues == 0:
        logger.info("All TOML config values are valid.")
    else:
        logger.warning(f"{issues} issue(s) found in TOML configuration.")

    return issues


if __name__ == "__main__":
    raise SystemExit(validate())