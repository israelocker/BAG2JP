"""Descubre el ID de personaje de Strike en BAG2 observando el selector.

Explora el grid de seleccion bidireccionalmente (izquierda/derecha) desde
cada posicion, registrando el ID de personaje en RAM para P2 en cada paso.
"""
import json
import os
import subprocess
import sys
import time
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import versus_navigation as nav
import versus_session as vs

GAME = vs.GAME
DISCOVERY_DIR = vs.project_config.assert_write_target(
    vs.load_config(), vs.CATALOG_TARGET.parent / "discovery-strike-id", role="work")


class DiscoverySession:
    def __init__(self, proc, bindings, run):
        self.proc = proc
        self.bindings = bindings
        self.run = run
        self.started = time.time()
        self.actions: list[dict] = []
        self.shots: list[str] = []
        self.checkpoints: dict[str, dict] = {}

    def assert_process(self) -> None:
        if self.proc.poll() is not None:
            raise RuntimeError("El juego cerro inesperadamente")

    def state(self) -> dict[str, int]:
        heartbeat = GAME / "bag2jp_frame.txt"
        watch = GAME / "bag2jp_watch.log"
        nav.check_freshness(heartbeat.stat().st_mtime, time.time(), self.started)
        if watch.stat().st_mtime < self.started:
            raise ValueError("El watch log pertenece a una ejecucion previa")
        lines = vs.tail(watch).splitlines()
        for line in reversed(lines):
            try:
                return nav.parse_watch(line)
            except ValueError:
                continue
        raise ValueError("No hay observacion de watch completa")

    def maybe_state(self) -> dict | None:
        try:
            return self.state()
        except (FileNotFoundError, ValueError):
            return None

    def wait(self, predicate, timeout: float = vs.TIMEOUT) -> dict:
        return nav.wait_until(self.maybe_state,
                              lambda v: v is not None and predicate(v), timeout)

    def key(self, side: int, action: str) -> None:
        self.assert_process()
        key = nav.key_for(self.bindings, side, action)
        vs.powershell(f"& {vs.ps_quote(vs.WINSHOT / 'postkey.ps1')} -Id {self.proc.pid} -Keys {vs.ps_quote(key)} -HoldMs 100 -GapMs 350 | Out-Null")
        self.actions.append({"player": side, "action": action, "key": key,
                             "time": round(time.time() - self.started, 3)})

    def shot(self, name: str) -> None:
        self.assert_process()
        path = self.run / f"{name}.png"
        if path.exists():
            raise FileExistsError(path)
        vs.powershell(f"& {vs.ps_quote(vs.WINSHOT / 'winshot.ps1')} -Ids {self.proc.pid} -Out {vs.ps_quote(path)} | Out-Null")
        self.shots.append(path.name)
        self.checkpoints[name] = self.state()

    def close(self) -> None:
        if self.proc.poll() is None:
            vs.assert_process_safe(self.proc.pid)
            vs.powershell(f"$p=Get-Process -Id {self.proc.pid}; $null=$p.CloseMainWindow(); if(-not $p.WaitForExit(15000)) {{throw 'El juego no cerro'}}")
            self.proc.wait(timeout=2)


def main() -> int:
    count = vs.powershell("@(Get-Process BAG2JP -ErrorAction SilentlyContinue).Count")
    if count != "0":
        print(f"ERROR: Sesion activa de BAG2JP ({count}). Abortando.")
        return 1

    bindings = nav.parse_bindings((GAME / "keybinds.ini").read_text(encoding="utf-8-sig"))

    env = {k: v for k, v in os.environ.items() if not k.startswith("BAG2JP_")}
    env["BAG2JP_ANIM_TRACE"] = "1"
    env["BAG2JP_WATCH"] = ",".join(f"{a:08X}:{s}" for a, s in nav.WATCHES.values())

    DISCOVERY_DIR.mkdir(parents=True, exist_ok=True)

    proc = subprocess.Popen([str(GAME / "BAG2JP.exe"), "--no-launcher"], cwd=GAME,
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    session = DiscoverySession(proc, bindings, DISCOVERY_DIR)
    results: list[dict] = []
    seen_ids: dict[int, dict] = {}

    try:
        # 1. Esperar arranque y menu
        print("Esperando secuencia de arranque...")
        observed = session.wait(lambda s: s["root"] in (5, 7), 300)
        if observed["root"] == 5:
            print("  Pantalla de apertura (root 5). Saltando con Start.")
            session.key(1, "start")
        session.wait(lambda s: s["root"] == 7, 60)
        time.sleep(1.3)

        # 2. Ir a Versus
        for _ in range(6):
            s = session.state()
            if s["root"] != 7:
                raise ValueError(f"Salio del menu: root={s['root']}")
            if s["menu"] == vs.MENU_VERSUS:
                break
            session.key(1, "down")
            session.wait(lambda c: c["menu"] != s["menu"])
        if session.state()["menu"] != vs.MENU_VERSUS:
            raise ValueError("No se alcanzo Versus")

        session.shot("versus-menu")
        session.key(1, "circle")
        session.wait(lambda s: s["root"] in vs.SELECT_ROOTS and s["mode"] == 2)
        nav.require_selector(session.state())
        session.shot("selector-entry")

        # 3. Exploracion del grid de P2 en las 4 direcciones
        def record(label: str) -> None:
            s = session.state()
            p2_id = nav.cursor(s, 2)
            p1_id = nav.cursor(s, 1)
            entry = {"label": label, "p2_char_id": p2_id, "p1_char_id": p1_id,
                     "root": s["root"], "mode": s["mode"],
                     "select_phase": s["select_phase"]}
            results.append(entry)
            seen_ids[p2_id] = entry
            session.shot(f"p2-{label}-id{p2_id}")
            print(f"  {label}: P2 id={p2_id}, P1 id={p1_id}")

        def explore_direction(direction_name: str, key_name: str, max_steps: int = 30) -> int:
            """Explora en una direccion, devolviendo el numero de pasos dados."""
            steps = 0
            for i in range(1, max_steps + 1):
                before = session.state()
                before_p2 = nav.cursor(before, 2)
                session.key(2, key_name)
                try:
                    session.wait(lambda c: nav.cursor(c, 2) != before_p2, 15)
                except TimeoutError:
                    print(f"  {direction_name}-{i}: fin de lista (sin cambio)")
                    break
                record(f"{direction_name}-{i}")
                steps += 1
            return steps

        record("start")
        max_steps = 30

        # Explorar izquierda
        print("\nExplorando hacia la izquierda...")
        left_steps = explore_direction("left", "left")

        # Volver al inicio yendo derecha
        print(f"\nRegresando al inicio ({left_steps} pasos a la derecha)...")
        for _ in range(left_steps):
            before = session.state()
            before_p2 = nav.cursor(before, 2)
            session.key(2, "right")
            session.wait(lambda c: nav.cursor(c, 2) != before_p2, 15)

        # Explorar derecha
        print("\nExplorando hacia la derecha...")
        right_steps = explore_direction("right", "right")

        # Volver al inicio yendo izquierda
        print(f"\nRegresando al inicio ({right_steps} pasos a la izquierda)...")
        for _ in range(right_steps):
            before = session.state()
            before_p2 = nav.cursor(before, 2)
            session.key(2, "left")
            session.wait(lambda c: nav.cursor(c, 2) != before_p2, 15)

        # Explorar arriba
        print("\nExplorando hacia arriba...")
        up_steps = explore_direction("up", "up")

        # Volver al inicio yendo abajo
        print(f"\nRegresando al inicio ({up_steps} pasos abajo)...")
        for _ in range(up_steps):
            before = session.state()
            before_p2 = nav.cursor(before, 2)
            session.key(2, "down")
            session.wait(lambda c: nav.cursor(c, 2) != before_p2, 15)

        # Explorar abajo
        print("\nExplorando hacia abajo...")
        down_steps = explore_direction("down", "down")

        # 4. Reporte
        print("\n=== RESUMEN DE DESCUBRIMIENTO ===")
        for r in results:
            print(f"  {r['label']}: P2_id={r['p2_char_id']} (root={r['root']}, mode={r['mode']})")

        unique_ids = sorted(seen_ids.keys())
        print(f"\nIDs unicos observados para P2: {unique_ids}")
        print(f"Total de posiciones visitadas: {len(results)}")

        report = {
            "discovery": results,
            "unique_ids": unique_ids,
            "total_positions": len(results),
            "screenshots": session.shots,
        }
        (DISCOVERY_DIR / "discovery-report.json").write_text(json.dumps(report, indent=2))
        print(f"\nReporte: {DISCOVERY_DIR / 'discovery-report.json'}")
        print(f"Capturas: {DISCOVERY_DIR}")

        return 0

    finally:
        try:
            session.close()
        except Exception as exc:
            print(f"Advertencia al cerrar: {exc}")
        print("Sesion cerrada.")


if __name__ == "__main__":
    raise SystemExit(main())
