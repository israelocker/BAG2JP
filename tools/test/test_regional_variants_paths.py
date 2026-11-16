"""Host checks for the regional-variant builder's declared locations."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import tools.workflow.project_config as pc

SPEC = importlib.util.spec_from_file_location(
    "build_regional_variants", Path(__file__).parents[1] / "bag1import/build_regional_variants.py")
regional = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(regional)

PROFILE = {
    "schema": 1,
    "regions": {
        "international": {"directories": {"1": "PLAYER1E"}},
        "japanese": {"directories": {"1": "PLAYER1"}},
    },
    "candidate_directory": "_work/candidates",
    "entries": [],
}
EXTRACTIONS = ("[inputs]\nbag1_usa_extraction = \"relocated_work/disc_usa\"\n"
               "bag1_jp_extraction = \"relocated_work/disc_jp\"\n"
               "bag2_disc = \"disc.bin\"\n")


class RegionalVariantLocationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.previous = regional.REPO
        regional.REPO = self.root
        self.addCleanup(setattr, regional, "REPO", self.previous)
        self.configure("[paths]\nwork_root = \"relocated_work\"\n" + EXTRACTIONS)
        for name in ("disc_usa", "disc_jp", "candidates"):
            (self.root / "relocated_work" / name).mkdir(parents=True, exist_ok=True)

    def configure(self, text):
        directory = self.root / "config"
        directory.mkdir(exist_ok=True)
        (directory / "project.toml").write_text(
            "schema_version = 1\n" + text, encoding="utf-8")

    def locations(self):
        return regional.profile_locations(PROFILE, pc.load_config(repo_root=self.root))

    def test_relocated_roots_replace_declared_work_member(self):
        found = self.locations()
        self.assertEqual(found["candidate_directory"], (self.root / "relocated_work/candidates").resolve())
        self.assertEqual(found["region_roots"]["international"],
                         (self.root / "relocated_work/disc_usa").resolve())
        self.assertEqual(found["region_roots"]["japanese"],
                         (self.root / "relocated_work/disc_jp").resolve())
        self.assertFalse((self.root / "_work").exists())

    def test_default_work_root_is_unchanged(self):
        self.configure("[paths]\nwork_root = \"_work\"\n" + EXTRACTIONS)
        self.assertEqual(self.locations()["candidate_directory"],
                         (self.root / "_work/candidates").resolve())

    def test_missing_work_root_is_a_configuration_error(self):
        self.configure("[harness]\nfps = 60\n")
        with self.assertRaises(pc.ConfigError):
            self.locations()

    def test_declared_locations_cannot_be_absolute_or_escape(self):
        for declared in (str(self.root / "elsewhere"), "_work/../outside", "_work/.. /outside"):
            with self.subTest(declared=declared):
                profile = dict(PROFILE, candidate_directory=declared)
                with self.assertRaises(ValueError):
                    regional.profile_locations(profile, pc.load_config(repo_root=self.root))

    def test_build_rejects_configuration_of_another_project(self):
        other = self.root / "other"
        (other / "config").mkdir(parents=True)
        (other / "config/project.toml").write_text(
            "schema_version = 1\n[paths]\nwork_root = \"relocated_work\"\n", encoding="utf-8")
        with self.assertRaises(pc.ConfigError):
            regional.build(PROFILE, self.root / "out", config=pc.load_config(repo_root=other))

    def test_build_reads_the_candidate_from_the_configured_root(self):
        entry = {"entry": 1, "chr": 0, "kind": 0, "class": "pack", "number": 1,
                 "source": "P_A.DFS", "rules": []}
        opened = []

        def fake_read_members(data):
            opened.append(data)
            raise ValueError("stop after the candidate read")

        self.addCleanup(setattr, regional, "stock_entries", regional.stock_entries)
        self.addCleanup(setattr, regional, "read_members", regional.read_members)
        regional.stock_entries = lambda disc, entries: {}
        regional.read_members = fake_read_members
        target = self.root / "relocated_work/candidates/entry_1_chr0_kind0.dfs"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"CANDIDATE")
        with self.assertRaisesRegex(ValueError, "stop after the candidate read") as caught:
            try:
                regional.build(dict(PROFILE, entries=[entry]), self.root / "out",
                               config=pc.load_config(repo_root=self.root))
            except FileNotFoundError as error:
                self.fail(f"candidate not read from the configured root: {error}")
        self.assertIsInstance(caught.exception, ValueError)
        self.assertEqual(opened, [b"CANDIDATE"])

    def test_segment_validator_rejects_absolute_and_escape(self):
        for bad in (str(self.root / "dir"), "_work/../dir", "_work/.. /dir", "", ".."):
            with self.subTest(segment=bad):
                with self.assertRaises(ValueError):
                    regional._trusted_segment(bad)
        self.assertEqual(regional._trusted_segment("PLAYER1E"), "PLAYER1E")

    def test_regional_directory_segment_must_not_escape(self):
        profile = dict(PROFILE,
                       regions={"international": {"directories": {"1": str(self.root / "outside")}},
                                "japanese": PROFILE["regions"]["japanese"]},
                       entries=[{"entry": 1, "chr": 0, "kind": 0, "class": "pack",
                                 "number": 1, "source": "P_A.DFS", "rules": []}])
        config = pc.load_config(repo_root=self.root)
        regional.stock_entries = lambda disc, entries: {}
        target = self.root / "relocated_work/candidates/entry_1_chr0_kind0.dfs"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"CANDIDATE")
        with self.assertRaises(ValueError):
            regional.build(profile, self.root / "out", config=config)

    def test_regional_source_must_not_escape(self):
        profile = dict(PROFILE, entries=[{"entry": 1, "chr": 0, "kind": 0, "class": "pack",
                                          "number": 1, "source": "_work/../P_A.DFS", "rules": []}])
        config = pc.load_config(repo_root=self.root)
        regional.stock_entries = lambda disc, entries: {}
        target = self.root / "relocated_work/candidates/entry_1_chr0_kind0.dfs"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"CANDIDATE")
        with self.assertRaises(ValueError):
            regional.build(profile, self.root / "out", config=config)


if __name__ == "__main__":
    unittest.main()
