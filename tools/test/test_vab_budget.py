"""Unit tests for voice VAB dedup, PS-ADPCM re-encoding and pitch compensation."""
import struct
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/bag1import"))

from preserve_announcer import append_cue, pack_banks, single_cue
from rebuild_dfs_members import read_members
from vab_budget import (Vab, decode_adpcm, dedupe_samples, encode_adpcm,
                        fit_voice_budget, payload, resample_samples)


def snr_db(reference: np.ndarray, candidate: np.ndarray) -> float:
    reference = reference.astype(np.float64)
    noise = reference - candidate.astype(np.float64)
    return 10 * np.log10(np.sum(reference ** 2) / max(np.sum(noise ** 2), 1.0))


class TestVabBudget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pack = ROOT / "_work/stage_import/gaso/stock_bio_entries/pack_a_p1.dfs"
        cls.stock = read_members(pack.read_bytes())[0][4]
        single = pack_banks([single_cue(cls.stock, 0x1907)])
        cls.duplicated = append_cue(single, cls.stock, 0x1908)

    def test_reencode_keeps_stock_layout_flags(self):
        sample = Vab(self.stock).samples[6]
        encoded = encode_adpcm(decode_adpcm(payload(sample)))
        self.assertEqual([encoded[1], encoded[17], encoded[-15], encoded[-31]],
                         [0, 4, 7, 1])

    def test_reencode_preserves_signal(self):
        original = decode_adpcm(payload(Vab(self.stock).samples[6]))
        again = decode_adpcm(payload(encode_adpcm(original)))
        self.assertGreater(snr_db(original, again), 25.0)

    def test_dedupe_shares_identical_samples(self):
        vab = Vab(dedupe_samples(self.duplicated))
        ids = [struct.unpack_from("<H", vab.head, o + 22)[0] for o in vab.tone_records()]
        self.assertEqual((len(vab.samples), ids), (1, [1, 1]))

    def test_dedupe_keeps_cue_table(self):
        self.assertEqual(Vab(dedupe_samples(self.duplicated)).table, Vab(self.duplicated).table)

    def test_dedupe_without_duplicates_is_byte_exact(self):
        self.assertEqual(dedupe_samples(self.stock), self.stock)

    def test_octave_resample_raises_center_by_twelve(self):
        before = Vab(self.stock)
        after = Vab(resample_samples(self.stock, [7], 1536))
        changed = [(before.head[o + 4], after.head[o + 4]) for o in before.tone_records()
                   if struct.unpack_from("<H", before.head, o + 22)[0] == 7]
        self.assertTrue(changed and all(new == old + 12 for old, new in changed))

    def test_octave_resample_halves_payload(self):
        before = len(payload(Vab(self.stock).samples[6]))
        after = len(payload(Vab(resample_samples(self.stock, [7], 1536)).samples[6]))
        self.assertLessEqual(abs(after - before // 2), 32)

    def test_resample_leaves_other_samples_byte_exact(self):
        after = Vab(resample_samples(self.stock, [7], 1536))
        self.assertEqual(after.samples[:6], Vab(self.stock).samples[:6])

    def test_resample_rejects_pitch_overflow(self):
        with self.assertRaises(ValueError):
            resample_samples(self.stock, [7], 1536 * 4)

    def test_fit_uses_lossless_dedup_when_enough(self):
        budget = len(Vab(self.duplicated).samples[0])
        _, units = fit_voice_budget(self.duplicated, [], budget)
        self.assertEqual(units, 0)

    def test_fit_resamples_only_non_kept_samples(self):
        vab = Vab(self.stock)
        keep = vab.samples[:10]
        fitted, units = fit_voice_budget(self.stock, keep, vab.body_bytes() - 2048)
        out = Vab(fitted)
        self.assertEqual((units > 0, out.samples[:10], out.body_bytes() <= vab.body_bytes() - 2048),
                         (True, keep, True))


if __name__ == "__main__":
    unittest.main()
