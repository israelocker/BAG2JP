"""Sequential, isolated Strike P1/P2 x A/B acceptance evidence; never auto-approve visuals."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

CASES = [
    dict(name='p1-a-heat1', side=1, costume='A', stage='HeatBAG1'),
    dict(name='p2-a-heat2', side=2, costume='A', stage='HeatBAG2'),
    dict(name='p1-b-heat2', side=1, costume='B', stage='HeatBAG2'),
    dict(name='p2-b-heat1', side=2, costume='B', stage='HeatBAG1'),
]


def validate_cases(cases):
    """A missing combination cannot silently shrink the promised matrix."""
    if len(cases) != 4 or len({c['name'] for c in cases}) != 4:
        raise ValueError('Four uniquely named cases required')
    if {(c['side'], c['costume']) for c in cases} != {(s, c) for s in (1, 2) for c in ('A', 'B')}:
        raise ValueError('Incomplete side/costume matrix')
    if {c['stage'] for c in cases} != {'HeatBAG1', 'HeatBAG2'}:
        raise ValueError('Both Heat stages required')


def observe_match(session, case, nav):
    """Observe native attack/fever traces and actual song exit; no RAM/state writes."""
    started = time.monotonic()
    offset = 0
    attacks, fever, shots = [], set(), []
    previous_attack = None
    next_regular = started + 20
    left = None
    trace = session.settings.game / 'bag2jp_anim_trace.log'
    while time.monotonic() - started < session.settings.finish_timeout:
        state = session.state()
        with trace.open('r', encoding='utf-8', errors='replace') as stream:
            stream.seek(offset)
            lines = stream.read().splitlines()
            offset = stream.tell()
        new_attack = False
        for line in lines:
            match = re.search(r'f(\d+) mode(\d+) phase ([0-9/]+) fever(\d+)', line)
            if not match or int(match[2]) != 2:
                continue
            frame = int(match[1])
            fever.add(int(match[4]))
            actor = re.search(rf'P{case["side"]} ch1 anim(\d+) req', line)
            if actor:
                attack = int(actor[1]) == 74
                if attack and previous_attack is not True:
                    attacks.append(frame)
                    new_attack = True
                previous_attack = attack
        if new_attack and len(shots) < 9 and nav.is_gameplay(state):
            name = f'attack-{len(shots):02d}'
            session.shot(name)
            shots.append({'name': name, 'trigger_trace_frame': attacks[-1]})
            # Follow this sequence; screenshots carry their actual observed checkpoints.
            for index in range(2):
                session.shot(f'{name}-follow-{index}')
        if state['root'] != nav.GAMEPLAY_ROOT and left is None:
            left = round(time.monotonic() - started, 1)
            session.shot('song-end')
        if nav.is_selector(state):
            session.shot('returned-selector')
            return dict(seconds=round(time.monotonic() - started, 1), left_battle=left,
                        return_root=state['root'], attack_trace_frames=attacks,
                        fever_values=sorted(fever), attack_captures=shots,
                        fever_verified=any(fever), visual_review='pending')
        if time.monotonic() >= next_regular:
            session.shot(f'match-{len(session.shots)}')
            next_regular += 20
        time.sleep(0.5)
    raise TimeoutError('Song did not return to selector')


def run_case(case, folder, runtime, catalog, nav, vs, settings):
    """Reuse the verified session driver and its settings/save isolation unchanged."""
    game = settings.game
    fixture = 'BAG2JP_TEST_STRIKE_ATTACK' if case['side'] == 1 else 'BAG2JP_TEST_HEAT_STRIKE_DUEL'
    first = 8000 if case['stage'] == 'HeatBAG1' else 6500
    frames = list(range(first, first + 8 * 120, 120))
    folder.mkdir()
    # The fixture and VRAM schedule are declared for this session only, never patched into Popen.
    session = vs.Session(folder, settings, fixtures={fixture: '1'})
    session.vram_dump_frames = tuple(frames)
    files = nav.IsolatedFiles(game, folder,
                             safe_to_restore=lambda: session.process is None or session.process.poll() is not None)
    result = dict(case=case, runtime_sha256=runtime, status='failed', fixture=fixture,
                  debug_fixtures=None, visual_review='pending', scheduled_vram_frames=frames)
    try:
        with files:
            try:
                if nav.sha256(game / 'BAG2JP.exe') != runtime:
                    raise ValueError('Runtime changed during batch')
                session.start()
                result['debug_fixtures'] = session.debug_fixtures
                session.menu()
                edges = nav.validated_edges(catalog, runtime)
                picks, characters, costumes = [], [], []
                for side in (1, 2):
                    character = 'Strike' if side == case['side'] else 'Heat'
                    costume = case['costume'] if character == 'Strike' else 'A'
                    picks.append(session.pick(side, character, 'BAG1', costume, edges))
                    characters.append(nav.resolve_character(character))
                    costumes.append(int(costume == 'B'))
                result['picks'] = picks
                session.match(case['stage'], characters, costumes)
                result['finish'] = observe_match(session, case, nav)
                result['status'] = 'machine_complete_awaiting_review'
                if not result['finish']['attack_trace_frames']:
                    result['status'] = 'incomplete_no_strike_attack'
            finally:
                for name in ('bag2jp_anim_trace.log', 'bag2jp_bag1_versions.log', 'bag2jp_watch.log',
                             'bag2jp_charsel_popup.log'):
                    vs.copy_current(game / name, folder, session.started)
                result['vram_files'] = []
                for frame in frames:
                    source = game / f'bag2jp_vram_{frame}.bin'
                    if vs.copy_current(source, folder, session.started):
                        result['vram_files'].append(source.name)
                session.close()
    except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError) as exc:
        result['error'] = str(exc)
    finally:
        result.update(restoration=files.restoration, checkpoints=session.checkpoints,
                      screenshots=session.shots)
        vs.save_result(folder, result, bool(session.shots))
    return result


def batch_status(results):
    """A finished batch still needs review; every case must finish and restore."""
    complete = len(results) == len(CASES) and all(
        result.get('status') == 'machine_complete_awaiting_review'
        and result.get('restoration', {}).get('verified')
        for result in results)
    return 'finished_awaiting_review' if complete else 'stopped_on_failure'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='explicitly authorize isolated game tests')
    parser.add_argument('--local-config', type=Path, default=None,
                        help='local TOML overlay; relative selections anchor to the repository')
    args = parser.parse_args(argv)
    validate_cases(CASES)
    if not args.execute:
        print(json.dumps(CASES, indent=2))
        return 0
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import versus_navigation as nav
    import versus_session as vs
    try:
        config = vs.load_config(local_config=args.local_config)
        settings = vs.resolve_settings(config)
    except vs.project_config.ConfigError as exc:
        parser.error(f'config error: {exc}')
    if vs.powershell('@(Get-Process BAG2JP -ErrorAction SilentlyContinue).Count',
                     settings.helper_timeout) != '0':
        print(json.dumps({'status': 'refused', 'error': 'Active game; no settings changed'}), flush=True)
        return 1
    runtime = nav.sha256(settings.game / 'BAG2JP.exe')
    catalog = json.loads(settings.catalog.read_text())
    nav.validated_edges(catalog, runtime)
    nav.verify_catalog_review(catalog)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    try:
        batch = vs.project_config.assert_write_target(
            config, settings.runs / f'{stamp}-strike-acceptance-batch', role='work')
    except vs.project_config.ConfigError as exc:
        parser.error(f'config error: {exc}')
    batch.mkdir(parents=True)
    report = dict(runtime_sha256=runtime, runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  configuration=settings.provenance(),
                  status='running', cases=[], limitations=['Actor lighting requires visual review',
                  'Ending and stage mode 0xB not covered by versus cases'])
    for case in CASES:
        try:
            result = run_case(case, batch / case['name'], runtime, catalog, nav, vs, settings)
        except Exception as exc:  # a case escaping its own contract must still leave an honest report
            result = dict(case=case, runtime_sha256=runtime, status='failed', restoration={},
                          error=f'{type(exc).__name__}: {exc}')
        report['cases'].append(result)
        (batch / 'batch.json').write_text(json.dumps(report, indent=2))
        print(json.dumps({'batch': str(batch), 'case': case['name'], 'status': result['status'],
                          'restored': result['restoration'].get('verified')}), flush=True)
        if result['status'] == 'failed' or not result['restoration'].get('verified'):
            break
    report['status'] = batch_status(report['cases'])
    (batch / 'batch.json').write_text(json.dumps(report, indent=2))
    return 0 if report['status'] == 'finished_awaiting_review' else 1


if __name__ == '__main__':
    raise SystemExit(main())
