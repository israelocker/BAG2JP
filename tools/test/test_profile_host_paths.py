"""Character profiles, caches and regional recipes carry no machine locations."""
import importlib.util, json, re, struct, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.workflow import project_config as pc


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / "bag1import" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


workflow = load("character_workflow")
regional = load("build_regional_variants")
MACHINE_PATH = re.compile(r'"[A-Za-z]:[/\\]')
# Locations that duplicate configuration keys must not live in tracked data.
CONFIG_OWNED = ("reference_runtime", "bag2_disc", "disc", "exefile", "extraction", "root")


def animation():
    data = bytearray(36)
    struct.pack_into("<I", data, 0, 28); struct.pack_into("<H", data, 4, 2); struct.pack_into("<I", data, 28, 4)
    return struct.pack("<I", len(data)) + data + bytes(4)


class TrackedDataTests(unittest.TestCase):
    def files(self):
        base = ROOT / "tools" / "bag1import"
        return sorted([*base.glob("profiles/*.json"), *base.glob("cache/*.json")])

    def test_no_machine_paths(self):
        for path in self.files():
            with self.subTest(file=path.name):
                self.assertEqual(MACHINE_PATH.findall(path.read_text(encoding="utf-8")), [])

    def test_no_configuration_owned_locations(self):
        def keys(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    yield key
                    yield from keys(value)
            elif isinstance(node, list):
                for value in node:
                    yield from keys(value)
        for path in self.files():
            with self.subTest(file=path.name):
                found = set(keys(json.loads(path.read_text(encoding="utf-8")))) & set(CONFIG_OWNED)
                self.assertEqual(found, set())


class CacheEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "config").mkdir()
        (self.root / "config" / "project.toml").write_text(
            'schema_version=1\n[paths]\nwork_root="relocated"\n[inputs]\nbag1_reference_runtime="runtime.bin"\n')
        (self.root / "source.bin").write_bytes(animation())
        (self.root / "runtime.bin").write_bytes(b"runtime")
        (self.root / "rom.bin").write_bytes(b"rom")
        self.evidence = self.root / "relocated" / "video.bin"
        self.evidence.parent.mkdir(); self.evidence.write_bytes(b"frames")
        catalog = {"schema": 1, "games": {"g": {"inputs": [{"file": "rom.bin", "sha256": workflow.file_sha(self.root / "rom.bin")}]}}}
        (self.root / "catalog.json").write_text(json.dumps(catalog))
        self.profile = self.root / "profile.json"; self.cache = self.root / "cache.json"
        self.profile.write_text(json.dumps({"schema": 1, "character": "alpha", "stage": "inventory",
                                            "source_animation_list": "source.bin", "game_catalog": "catalog.json",
                                            "exceptions": []}))

    def test_evidence_is_recorded_as_a_declared_location(self):
        workflow.record_cache(self.profile, self.root, self.cache, [self.evidence])
        files = [item["file"] for item in json.loads(self.cache.read_text())["evidence"]]
        self.assertEqual(files, ["_work/video.bin"])
        self.assertEqual(workflow.check_cache(self.profile, self.root, self.cache)["status"], "hit")

    def test_evidence_outside_the_project_is_rejected(self):
        outside = Path(tempfile.mkdtemp()); self.addCleanup(lambda: (outside / "v.bin").unlink(missing_ok=True) or outside.rmdir())
        (outside / "v.bin").write_bytes(b"x")
        with self.assertRaises(ValueError):
            workflow.record_cache(self.profile, self.root, self.cache, [outside / "v.bin"])

    def test_absolute_legacy_evidence_misses(self):
        workflow.record_cache(self.profile, self.root, self.cache, [self.evidence])
        record = json.loads(self.cache.read_text())
        record["evidence"][0]["file"] = str(self.evidence)
        self.cache.write_text(json.dumps(record))
        self.assertEqual(workflow.check_cache(self.profile, self.root, self.cache)["status"], "miss")


class RegionalDiscTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "config").mkdir()
        self.addCleanup(setattr, regional, "REPO", regional.REPO)
        self.addCleanup(setattr, regional, "stock_entries", regional.stock_entries)
        regional.REPO = self.root
        for name in ("usa", "jp", "cand"):
            (self.root / "_work" / name).mkdir(parents=True)
        self.profile = {"schema": 1, "candidate_directory": "_work/cand", "entries": [],
                        "regions": {"international": {"directories": {}},
                                    "japanese": {"directories": {}}}}

    def config(self, extra):
        (self.root / "config" / "project.toml").write_text(
            'schema_version=1\n[paths]\nwork_root="_work"\n[inputs]\n'
            'bag1_usa_extraction="_work/usa"\nbag1_jp_extraction="_work/jp"\n' + extra)
        return pc.load_config(repo_root=self.root)

    def test_disc_comes_from_configuration(self):
        seen = []
        regional.stock_entries = lambda disc, entries: seen.append(Path(disc)) or {}
        regional.build(self.profile, self.root / "out", config=self.config('bag2_disc="discs/bag2.bin"\n'))
        self.assertEqual(seen, [(self.root / "discs" / "bag2.bin").resolve()])

    def test_missing_disc_key_raises(self):
        regional.stock_entries = lambda disc, entries: {}
        with self.assertRaises(pc.ConfigError):
            regional.build(self.profile, self.root / "out", config=self.config(""))


if __name__ == "__main__":
    unittest.main()
