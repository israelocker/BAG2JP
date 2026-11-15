"""Gas-O extraction selection without conversion, packages or game processes."""
from contextlib import redirect_stdout
import copy
import io
import json
import inspect
from pathlib import Path
from unittest.mock import MagicMock, patch

from tools.test.test_gaso_hud import ROOT
from tools.workflow import project_config as pc
from tools.workflow.test_project_config import ConfigFixture, working_directory
import build_gaso_assets as builder


class GasoSourceConfigTests(ConfigFixture):
    def setUp(self):
        super().setUp()
        self.profile = json.loads((ROOT / 'tools/bag1import/profiles/gaso.json').read_text(encoding='utf-8'))
        self.original = copy.deepcopy(self.profile)
        self.write_local('[inputs]\n'
                         'bag1_usa_extraction="relocated usa ñ"\n'
                         'bag1_jp_extraction="relocated jp &"\n'
                         'gaso_profile="profile.json"\n'
                         'gaso_stock_bio="stock"\n'
                         'gaso_stock_fever="fever"\n'
                         'gaso_motions="motions.bin"\n'
                         '[paths]\n'
                         'gaso_out_usa="owned-output"\n'
                         'gaso_out_jp="owned-output"\n')
        self.local_profile = self.root / 'profile.json'
        self.local_profile.write_text(json.dumps(self.profile), encoding='utf-8')
        # 'changed'/'wrong' exist so that a reload yields a wrong path, not a ConfigError.
        for name in ('relocated usa ñ', 'relocated jp &', 'changed', 'wrong'):
            (self.root / name).mkdir()
        self.root.joinpath('stock').mkdir()
        self.root.joinpath('fever').mkdir()
        self.root.joinpath('motions.bin').write_bytes(b'motions')

    def sources(self, region, **kwargs):
        self.assertIn('config', inspect.signature(builder.region_sources).parameters,
                      'reader must accept an immutable resolved configuration')
        return builder.region_sources(region, config=kwargs.pop('config', self.load()),
                                      profile=self.profile, **kwargs)

    def test_config_controls_roots_but_profile_controls_regional_layout(self):
        with working_directory(self.root.parent):
            usa, packs_usa, models_usa = self.sources('usa')
            jp, packs_jp, models_jp = self.sources('jp')
        self.assertEqual(usa, self.root / 'relocated usa ñ')
        self.assertEqual(jp, self.root / 'relocated jp &')
        self.assertEqual(packs_usa, {'costume_a':'PLAYER1E', 'costume_b':'PLAYER3E'})
        self.assertEqual(packs_jp, {'costume_a':'PLAYER1', 'costume_b':'PLAYER3'})
        self.assertEqual(models_usa, {'costume_a':'PLAYER2', 'costume_b':'PLAYER4'})
        self.assertEqual(models_jp, models_usa)
        self.assertEqual(self.profile, self.original)

    def test_only_the_used_region_is_required_and_no_profile_root_fallback_exists(self):
        self.write_local('[inputs]\nbag1_usa_extraction="relocated usa ñ"\n'
                         'gaso_profile="profile.json"\n'
                         'gaso_stock_bio="stock"\n'
                         'gaso_stock_fever="fever"\n'
                         'gaso_motions="motions.bin"\n')
        try:
            usa = self.sources('usa')[0]
        except pc.ConfigError as error:
            self.fail(f"USA must not require the unused JP root: {error}")
        self.assertEqual(usa, self.root / 'relocated usa ñ')
        with self.assertRaises(pc.ConfigError):
            self.sources('jp')

    def test_snapshot_is_not_reloaded_after_overlay_changes(self):
        config = self.load()
        self.write_local('[inputs]\nbag1_usa_extraction="wrong"\nbag1_jp_extraction="wrong"\n'
                         'gaso_profile="profile.json"\n'
                         'gaso_stock_bio="stock"\n'
                         'gaso_stock_fever="fever"\n'
                         'gaso_motions="motions.bin"\n')
        self.assertEqual(self.sources('usa', config=config)[0], self.root / 'relocated usa ñ')
        self.assertEqual(self.sources('jp', config=config)[0], self.root / 'relocated jp &')

    def test_missing_announcer_root_fails_before_build_output_is_created(self):
        self.write_local('[inputs]\nbag1_usa_extraction="relocated usa ñ"\n'
                         'bag1_jp_extraction="absent jp"\n'
                         'gaso_profile="profile.json"\n'
                         'gaso_stock_bio="stock"\n'
                         'gaso_stock_fever="fever"\n'
                         'gaso_motions="motions.bin"\n')
        with self.assertRaisesRegex(pc.ConfigError, 'absent jp'):
            self.sources('jp')
        output = self.root / 'candidate'
        self.assertIn('config', inspect.signature(builder.build).parameters)
        with patch.object(builder, 'read_members', side_effect=AssertionError('before conversion')):
            with self.assertRaises(pc.ConfigError):
                builder.build('usa', output, config=self.load())
        self.assertFalse(output.exists())

    def test_selected_overlay_reaches_build_without_generating_a_package(self):
        self.assertIn('argv', inspect.signature(builder.main).parameters)
        self.write_local('[inputs]\n'
                         'bag1_jp_extraction=' + json.dumps(str(self.root / 'relocated jp &')) + '\n'
                         'gaso_profile="profile.json"\n'
                         'gaso_stock_bio="stock"\n'
                         'gaso_stock_fever="fever"\n'
                         'gaso_motions="motions.bin"\n'
                         '[paths]\n'
                         'gaso_out_usa="owned-output"\n'
                         'gaso_out_jp="owned-output"\n')
        output = self.root / 'candidate'
        with patch.object(builder, 'build') as build:
            builder.main(['--local-config', str(self.local), '--region', 'jp', '--out-dir', str(output)])
        self.assertEqual(build.call_args.args, ('jp', output))
        config = build.call_args.kwargs['config']
        self.assertIn('inputs.bag1_jp_extraction', config.values)
        self.assertEqual(config.values['inputs.bag1_jp_extraction'], self.root / 'relocated jp &')
        self.assertEqual(config.input_files['local'], str(self.local))
        self.assertFalse(output.exists())

    def test_build_uses_one_snapshot_for_model_and_independent_announcer_region(self):
        profile_path = self.root / 'profile.json'
        profile_path.write_text(json.dumps(self.profile), encoding='utf-8')
        self.write_local('[inputs]\nbag1_usa_extraction="relocated usa ñ"\n'
                         'bag1_jp_extraction="relocated jp &"\n'
                         'gaso_profile="profile.json"\n'
                         'gaso_stock_bio="stock"\n'
                         'gaso_stock_fever="fever"\n'
                         'gaso_motions="motions.bin"\n')
        config = self.load()
        original = builder.region_sources
        calls = []
        def sources(region, **kwargs):
            result = original(region, **kwargs)
            calls.append((region, result[0], kwargs['config'], copy.deepcopy(kwargs['profile'])))
            self.write_local('[inputs]\nbag1_usa_extraction="changed"\nbag1_jp_extraction="changed"\n')
            profile_path.write_text('{}', encoding='utf-8')
            return result
        class StopBeforeConversion(Exception):
            pass
        output = self.root.parent / 'owned-output'
        stock = self.root / 'stock'
        (stock / 'pack_a_p1.dfs').write_bytes(b'owned sentinel, never decoded')
        with patch.object(builder, 'region_sources', side_effect=sources), \
                patch.object(builder, 'read_members', side_effect=StopBeforeConversion):
            with self.assertRaises(StopBeforeConversion):
                builder.build('usa', output, config=config)
        self.assertEqual([call[:2] for call in calls], [('usa', self.root / 'relocated usa ñ'),
                                                        ('jp', self.root / 'relocated jp &')])
        self.assertTrue(all(call[2] is config and call[3] == self.original for call in calls))
        self.assertEqual(list(output.iterdir()), [])

    def test_bad_cli_configuration_exits_two_before_build(self):
        with patch.object(builder, 'build') as build:
            with self.assertRaises(SystemExit) as error:
                builder.main(['--local-config', str(self.root / 'missing.toml')])
        self.assertEqual(error.exception.code, 2)
        build.assert_not_called()

    def test_unknown_regions_are_rejected_without_forming_arbitrary_keys(self):
        for region in ('../usa', 'USA', '', 'eu'):
            with self.subTest(region=region), self.assertRaises(pc.ConfigError):
                self.sources(region)

    def test_configured_but_absent_root_fails_before_build_output_is_created(self):
        self.write_local('[inputs]\nbag1_usa_extraction="relocated usa ñ"\n'
                         'bag1_jp_extraction="absent jp"\n'
                         'gaso_profile="profile.json"\n'
                         'gaso_stock_bio="stock"\n'
                         'gaso_stock_fever="fever"\n'
                         'gaso_motions="motions.bin"\n')
        with self.assertRaisesRegex(pc.ConfigError, 'absent jp'):
            self.sources('jp')
        output = self.root / 'candidate'
        with patch.object(builder, 'read_members', side_effect=AssertionError('before conversion')):
            with self.assertRaises(pc.ConfigError):
                builder.build('usa', output, config=self.load())
        self.assertFalse(output.exists())

    def full_build(self, region, profile):
        """Run build to completion on owned fixtures; record regional reads, cues and outputs."""
        profile_path = self.root / 'profile.json'
        profile_path.write_text(json.dumps(profile), encoding='utf-8')
        layout = profile['source_layout']
        directories = {d for r in layout['regions'].values() for d in r['pack_directories'].values()}
        directories |= {layout[costume]['model_directory'] for costume in ('costume_a', 'costume_b')}
        files = ('P_GAS_A1.DFS', 'P_GAS_B1.DFS', 'P_GAS_A3.DFS', 'P_GAS_B3.DFS',
                 'P_GAS_A2.DFS', 'P_GAS_A4.DFS')
        # Decoys in both roots and every directory turn a wrong path into a wrong label.
        for root_name in ('relocated usa ñ', 'relocated jp &'):
            for directory in directories:
                (self.root / root_name / directory).mkdir(exist_ok=True)
                for name in files:
                    (self.root / root_name / directory / name).write_bytes(
                        f'{root_name}/{directory}/{name}'.encode())
        stock = self.root / 'stock'
        for name in ('pack_a_p1.dfs', 'pack_a_p2.dfs'):
            (stock / name).write_bytes(f'stock/{name}'.encode())
        fever = self.root / 'fever'
        for name in ('000.bin', '001.bin'):
            (fever / name).write_bytes(name.encode())
        motions = self.root / 'motions.bin'
        motions.write_bytes(b'motions')
        self.write_local('[inputs]\n'
                         'bag1_usa_extraction="relocated usa ñ"\n'
                         'bag1_jp_extraction="relocated jp &"\n'
                         'gaso_profile="profile.json"\n'
                         'gaso_stock_bio="stock"\n'
                         'gaso_stock_fever="fever"\n'
                         'gaso_motions="motions.bin"\n')
        config = self.load()
        reads, cues, written = [], [], []
        def read_members(raw):
            if not reads:  # any later reload would observe these changed inputs
                self.write_local('[inputs]\nbag1_usa_extraction="changed"\nbag1_jp_extraction="changed"\n')
                profile_path.write_text('{}', encoding='utf-8')
            reads.append(raw.decode())
            return [raw] * 8, None
        def rebase(raw, old, new):
            cues.append(('rebase', old, new)); return raw, 11
        def rename(names, source, target, record):
            cues.append(('voice', names.decode(), source, target)); return names
        def replace(bank, target, names, source):
            cues.append(('vs', names.decode(), source, target)); return bank
        output = self.root.parent / 'owned-output'
        stubs = dict(read_members=read_members, rebase_sedt=rebase, rename_cue=rename, replace_cue=replace,
                     patch_gaso_dbi=lambda raw: raw, cue_record=lambda bank, target: b'',
                     append_cue=lambda bank, clip, target: bank, Vab=MagicMock(),
                     fit_voice_budget=lambda bank, samples, budget: (bank, 0),
                     retarget=lambda source, reference: source,
                     build_hud_texture=lambda source, reference, label: source,
                     convert=lambda source: (source, {}, None), check_bag2=lambda data: 0,
                     anim_list=lambda raw: [], build_fever=lambda source, count: b'fever',
                     write_entry=lambda out_dir, name, members: written.append(name))
        with patch.multiple(builder, **stubs), redirect_stdout(io.StringIO()):
            try:
                builder.build(region, output, config=config)
            except Exception as error:  # every escape is an assertion failure, not an ERROR
                self.fail(f'build must complete on owned fixtures: {error!r}')
        return reads, cues, written

    def assert_regional_reads(self, profile, region, announcer_root, reads, cues, written):
        layout, announcer = profile['source_layout'], profile['announcer']
        root = {'usa': 'relocated usa ñ', 'jp': 'relocated jp &'}[region]
        packs = layout['regions'][region]['pack_directories']
        names = f"{announcer_root}/{layout['regions'][announcer['source_region']]['pack_directories']['costume_a']}/P_GAS_A1.DFS"
        self.assertEqual(reads, [
            'stock/pack_a_p1.dfs', 'stock/pack_a_p2.dfs',
            f"{root}/{packs['costume_a']}/P_GAS_A1.DFS", f"{root}/{packs['costume_a']}/P_GAS_B1.DFS",
            f"{root}/{packs['costume_b']}/P_GAS_A3.DFS", f"{root}/{packs['costume_b']}/P_GAS_B3.DFS",
            names,
            f"{root}/{layout['costume_a']['model_directory']}/P_GAS_A2.DFS",
            f"{root}/{layout['costume_b']['model_directory']}/P_GAS_A4.DFS"])
        self.assertEqual(cues, [('rebase', 0x1800, 0x6900)]
                         + [('voice', names, int(s, 16), int(t, 16)) for t, s in announcer['voice_cues'].items()]
                         + [('vs', names, int(s, 16), int(t, 16))
                            for side in announcer['vs_cues'].values() for t, s in side.items()])
        self.assertEqual(written, [
            'entry_53_pack_a_p1.dfs', 'entry_54_pack_a_p2.dfs', 'entry_125_pack_b_p1.dfs',
            'entry_126_pack_b_p2.dfs', 'entry_89_model_a_p1.dfs', 'entry_90_model_a_p2.dfs',
            'entry_161_model_b_p1.dfs', 'entry_162_model_b_p2.dfs',
            f"entry_{profile['target_entries']['fever_choreography'][0]}_choreography_a.dfs"])

    def test_actual_profile_usa_build_reads_usa_assets_and_jp_announcer(self):
        reads, cues, written = self.full_build('usa', self.profile)
        self.assert_regional_reads(self.profile, 'usa', 'relocated jp &', reads, cues, written)

    def test_actual_profile_jp_build_does_not_require_usa_root(self):
        self.write_local('[inputs]\nbag1_jp_extraction="relocated jp &"\n'
                         'gaso_profile="profile.json"\n'
                         'gaso_stock_bio="stock"\n'
                         'gaso_stock_fever="fever"\n'
                         'gaso_motions="motions.bin"\n')
        reads, cues, written = self.full_build('jp', self.profile)
        self.assert_regional_reads(self.profile, 'jp', 'relocated jp &', reads, cues, written)

    def test_synthetic_profile_drives_directories_and_usa_announcer_for_jp_build(self):
        profile = copy.deepcopy(self.profile)
        layout = profile['source_layout']
        layout['regions']['usa']['pack_directories'] = {'costume_a': 'USA_A', 'costume_b': 'USA_B'}
        layout['regions']['jp']['pack_directories'] = {'costume_a': 'JP_A', 'costume_b': 'JP_B'}
        layout['costume_a']['model_directory'], layout['costume_b']['model_directory'] = 'MODEL_A', 'MODEL_B'
        profile['announcer']['source_region'] = 'usa'
        reads, cues, written = self.full_build('jp', profile)
        self.assert_regional_reads(profile, 'jp', 'relocated usa ñ', reads, cues, written)
