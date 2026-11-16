"""Configured locations for standalone host scripts (Windows or WSL); no location defaults live here."""
from functools import lru_cache
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.workflow.project_config import ProjectConfig, load_config, require_paths  # noqa: E402


@lru_cache(maxsize=1)
def _config() -> ProjectConfig:
    return load_config(repo_root=ROOT)


def path(key: str, *, config: ProjectConfig | None = None) -> Path:
    """Return the path registered under ``key``; a missing key raises ConfigError."""
    value, = require_paths(config if config is not None else _config(), (key,))
    return value


def text(key: str, *, config: ProjectConfig | None = None) -> str:
    """POSIX-style text form for scripts that build paths with f-strings."""
    return path(key, config=config).as_posix()
