"""Campaign (story) mode test session built on the versus harness.

Reuses Session/IsolatedFiles: backed-up settings, temporary controls, copied cards.
The first campaign rival is forced through the BAG2JP_TEST_CAMPAIGN_RIVAL fixture
(anim-trace debug plugin); BAG1 versions come from isolated mods/state.toml values.
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from pathlib import Path

import versus_session as vs  # sets up the repository import path
from tools.workflow import project_config
import versus_navigation as nav

MENU_CAMPAIGN = 0


def set_versions(game: Path, values: dict[str, str]) -> None:
    """Write bag1-heat option values into the (already backed-up) state.toml."""
    path = game / "mods" / "state.toml"
    text = path.read_text(encoding="utf-8-sig")
    block = re.search(r'id = "bag1-heat"\n.*?\[feature\.values\]\n((?:\w+ = "[^"]*"\n)*)', text, re.S)
    if block is None:
        raise ValueError("bag1-heat values block not found")
    current = dict(re.findall(r'(\w+) = "([^"]*)"', block.group(1)))
    current.update(values)
    body = "".join(f'{key} = "{value}"\n' for key, value in current.items())
    path.write_text(text[:block.start(1)] + body + text[block.end(1):], encoding="utf-8")


def open_session(tag: str, rival: int | None, versions: dict[str, str],
                 extra: dict[str, str] | None = None,
                 watch: list[tuple[int, int]] | None = None):
    """Prepare isolated files and launch; caller must close session then files."""
    config = vs.load_config()
    settings = vs.resolve_settings(config)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run = project_config.assert_write_target(config, settings.runs / f"{stamp}-{tag}", role="work")
    run.mkdir(parents=True, exist_ok=False)
    fixtures = {} if rival is None else {"BAG2JP_TEST_CAMPAIGN_RIVAL": str(rival)}
    fixtures.update(extra or {})
    session = vs.Session(run, settings, fixtures=fixtures)
    session.watch_extra = list(watch or [])
    files = nav.IsolatedFiles(settings.game, run,
                              safe_to_restore=lambda: session.process is None or session.process.poll() is not None)
    files.__enter__()
    try:
        set_versions(settings.game, versions)
        session.start()
    except BaseException:
        session.close()
        files.__exit__(None, None, None)
        raise
    return session, files


def enter_menu(session: vs.Session, index: int) -> None:
    """Reach the title menu and confirm the given menu index."""
    observed = session.wait(lambda s: s["root"] in (5, vs.MENU_ROOT), 60)
    if observed["root"] == 5:
        session.key(1, "start")
    session.wait(lambda s: s["root"] == vs.MENU_ROOT, 30)
    time.sleep(session.settings.menu_fade)
    for _ in range(6):
        state = session.state()
        if state["menu"] == index:
            break
        session.key(1, "up" if state["menu"] > index else "down")
        session.wait(lambda s: s["menu"] != state["menu"])
    if session.state()["menu"] != index:
        raise ValueError(f"Menu index {index} not reached")
    session.shot(f"menu-{index}")
    session.key(1, "circle")
