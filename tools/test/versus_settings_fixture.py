"""Owned disposable configuration trees for versus harness tests; never game files."""
from pathlib import Path
import tempfile

from tools.workflow import project_config

REPO = Path(__file__).resolve().parents[2]
LOCAL = ('schema_version = 1\n[paths]\nexperimental_install = "game"\nstable_install = "stable"\n'
         '[tools]\nwinshot_root = "winshot"\n')


def relocated_root(test) -> Path:
    """A different repository root per test, removed by the test's cleanup."""
    parent, = project_config.require_paths(project_config.load_config(repo_root=REPO), ("paths.work_root",))
    parent.mkdir(exist_ok=True)
    temporary = tempfile.TemporaryDirectory(prefix="versus-config-", dir=parent)
    test.addCleanup(temporary.cleanup)
    return Path(temporary.name).resolve()


def build_config(root: Path, local: str = LOCAL) -> project_config.ProjectConfig:
    """Copy the reviewed common TOML into a relocated root and select owned install roots."""
    (root / "config").mkdir()
    (root / "config/project.toml").write_bytes((REPO / "config/project.toml").read_bytes())
    work, = project_config.require_paths(project_config.load_config(repo_root=REPO), ("paths.work_root",))
    for name in ("game", "stable", "winshot", work.relative_to(REPO)):
        (root / name).mkdir(parents=True, exist_ok=True)
    (root / "config/project.local.toml").write_text(local, encoding="utf-8", newline="\n")
    return project_config.load_config(repo_root=root)


def make_settings(test, versus_session, local: str = LOCAL):
    """Resolve immutable harness settings through the production resolver."""
    return versus_session.resolve_settings(build_config(relocated_root(test), local))
