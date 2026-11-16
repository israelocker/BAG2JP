"""Authentic CAUGHT bytes in the real allocator/snapshot arena, not gameplay."""
import hashlib
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.test.test_caught_loan import ROOT, linux_path
from tools.bag1import import build_caught_bank
from tools.bag1import.animlib import info

CLIPS = (
    ('heat', 'aba71e3806dcbb731f6bc4df87437d8845491d66ae1cf94a1671a8650db93fad'),
    ('strike', 'ce96572206a41ce5b73200b5d62fc387338b82341f0f43afecb7982eb28cf8c9'),
    ('gaso', '38263c28e1607d57fa5fc0ff2e5221978a1989a0e2ce19991ac771cb6b01c55a'),
)


class CaughtBankSourceTest(unittest.TestCase):
    def test_runtime_metadata_clamps_pose_without_changing_motion(self) -> None:
        """Only metadata byte5 changes; native controller then holds the final frame."""
        clips = build_caught_bank.extract_clips()
        text = build_caught_bank.generated_text(clips)
        array = text.split('b1cc_data[B1CC_BANK_BYTES] = {', 1)[1].split('}', 1)[0]
        actual = bytes(int(v, 16) for v in re.findall(r'0x([0-9a-f]{2})', array))
        offset = 0
        for character, source in clips:
            with self.subTest(character=character):
                _header, _events, metadata, _end = info(source)
                expected = bytearray(source)
                expected[metadata + 5] = 1
                self.assertEqual(actual[offset:offset + len(source)], bytes(expected))
                self.assertEqual(source[metadata + 5], 0)  # original is immutable
            offset += len(source)

    def test_generated_bank_is_identical_to_pinned_original_sources(self) -> None:
        """Source extraction must match both prior decoder fixtures and the bank."""
        clips = build_caught_bank.extract_clips()
        self.assertEqual([character for character, _clip in clips], [0, 1, 9])
        self.assertEqual([len(clip) for _character, clip in clips], [348, 352, 348])
        for (_character, clip), (name, digest) in zip(clips, CLIPS, strict=True):
            with self.subTest(name=name):
                prior = ROOT / '_work/gaso/owned-decoder-input' / (name + '.bin')
                self.assertEqual(clip, prior.read_bytes())
                self.assertEqual(hashlib.sha256(clip).hexdigest(), digest)
        actual = build_caught_bank.OUTPUT.read_bytes()
        self.assertEqual(actual, build_caught_bank.generated_text(clips).encode('ascii'))

    def test_changed_source_is_rejected_before_extraction(self) -> None:
        """A changed source must not silently regenerate trusted motion data."""
        with tempfile.TemporaryDirectory(dir=ROOT / '_work') as directory:
            path = Path(directory) / 'source.dfs'
            source = ROOT / '_work/bag1_disc_full/PLAYER2/P_HEATA2.DFS'
            data = source.read_bytes()
            path.write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
            contract = json.loads(build_caught_bank.CONTRACT.read_text(encoding='utf-8'))
            contract['clips'][0]['source'] = path.relative_to(ROOT).as_posix()
            temporary = Path(directory) / 'contract.json'
            temporary.write_text(json.dumps(contract), encoding='utf-8')
            with patch.object(build_caught_bank, 'CONTRACT', temporary):
                with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):
                    build_caught_bank.extract_clips()


class CaughtBankTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Compile production bank plus real framework memory with title API doubles."""
        cls.directory = tempfile.TemporaryDirectory(dir=ROOT / '_work')
        cls.addClassCleanup(cls.directory.cleanup)
        directory = Path(cls.directory.name)
        cls.binary = linux_path(directory / 'caught-bank')
        cls.expected = directory / 'expected.bin'
        clips = []
        for name, digest in CLIPS:
            data = (ROOT / '_work/gaso/owned-decoder-input' / (name + '.bin')).read_bytes()
            if hashlib.sha256(data).hexdigest() != digest:
                raise AssertionError('Authentic fixture changed: ' + name)
            # Independent expectation: original motion, only metadata+5 adapted.
            _header, _events, metadata, _end = info(data)
            expected = bytearray(data)
            expected[metadata + 5] = 1
            clips.append(bytes(expected))
        cls.expected.write_bytes(b''.join(clips))
        framework = ROOT.parent / 'BAG2JP-codex-build/BAG2JP/psxrecomp/runtime'
        source = ROOT / 'mods-src/bag2jp.feature.bag1-content'
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                        '-Wall', '-Wextra', '-Werror', '-O2', '-flto',
                        '-ffunction-sections', '-fdata-sections',
                        '-I' + linux_path(source), '-I' + linux_path(framework / 'include'),
                        '-I' + linux_path(framework / 'src'),
                        linux_path(ROOT / 'tools/test/caught_bank_harness.c'),
                        linux_path(source / 'bag2jp_caught_bank.c'),
                        linux_path(framework / 'src/psx_ram_geometry.c'),
                        '-Wl,--gc-sections', '-o', cls.binary], check=True)

    def run_scenario(self, scenario: int, kind: int = 0) -> None:
        """Execute an isolated allocator lifetime and require all C assertions."""
        result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', self.binary,
                                 str(scenario), str(kind), linux_path(self.expected)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_authentic_per_rival_bytes_and_repeated_prepare_keep_one_allocation(self) -> None:
        self.run_scenario(0)

    def test_failed_or_invalid_allocation_never_accesses_guest_or_retries(self) -> None:
        for kind in range(5):
            with self.subTest(kind=kind):
                self.run_scenario(1, kind)

    def test_failed_copy_never_exposes_a_ready_clip_or_rewrites(self) -> None:
        self.run_scenario(2)

    def test_corruption_is_not_repaired_and_real_snapshot_restores_readiness(self) -> None:
        for kind in range(2):
            with self.subTest(kind=kind):
                self.run_scenario(3, kind)

    def test_ineligible_lookup_keeps_output_and_guest_unchanged(self) -> None:
        for kind in range(5):
            with self.subTest(kind=kind):
                self.run_scenario(4, kind)


if __name__ == '__main__':
    unittest.main()
