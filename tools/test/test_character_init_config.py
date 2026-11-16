"""Profile initialization and cache destinations resolve through configuration."""
import importlib.util, json, struct, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.workflow import project_config as pc

spec = importlib.util.spec_from_file_location(
    "character_workflow", ROOT / "tools/bag1import/character_workflow.py")
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


def animation(event=0, motion=0):
    data = bytearray(36)
    struct.pack_into("<I", data, 0, 28); struct.pack_into("<H", data, 4, 2)
    struct.pack_into("<I", data, 28, 4); data[8] = motion; data[32] = event
    return struct.pack("<I", len(data)) + data + bytes(4)


def archive(motion):
    return struct.pack("<4sI4I", b"DFS_", 2, 24, 4, 28, len(motion)) + bytes(4) + motion


def sha(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class InitProfileConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / "relocated_work"
        self.work.mkdir(parents=True)
        (self.root / "config").mkdir()
        (self.work / "archive.mem").write_bytes(archive(animation()))
        (self.work / "runtime.bin").write_bytes(b"runtime")
        (self.work / "rom.bin").write_bytes(b"base game")
        self.catalog = {"schema": 1, "games": {"game": {"inputs": [
            {"file": "_work/rom.bin", "sha256": sha(self.work / "rom.bin")}]}}}
        (self.work / "catalog.json").write_text(json.dumps(self.catalog), encoding="utf-8")
        self.profile = self.root / "profiles" / "alpha.json"

    def configure(self, text):
        (self.root / "config" / "project.toml").write_text(text, encoding="utf-8")

    def initialize(self, **overrides):
        arguments = dict(source_archive="_work/archive.mem", source_list="_work/source.bin",
                         runtime="_work/runtime.bin", catalog="_work/catalog.json")
        arguments.update(overrides)
        config = pc.load_config(repo_root=self.root)
        return workflow.init_profile(self.root, self.profile, "alpha", config=config, **arguments)

    def test_relocated_work_root_initializes_profile(self):
        self.configure('schema_version=1\n[paths]\nwork_root="relocated_work"\n[inputs]\n'
                       'bag1_reference_runtime="relocated_work/runtime.bin"\n')
        result = self.initialize()
        self.assertEqual(result["animation_count"], 1)
        document = json.loads(self.profile.read_text(encoding="utf-8"))
        self.assertEqual(document["source_animation_list"], "_work/source.bin")
        self.assertEqual(document["game_catalog"], "_work/catalog.json")
        self.assertFalse((self.root / "_work").exists())
        config = pc.load_config(repo_root=self.root)
        profile, _ = workflow.load_profile(self.profile, self.root, config=config)
        self.assertEqual(profile["character"], "alpha")

    def test_recorded_declarations_do_not_depend_on_work_location(self):
        self.configure('schema_version=1\n[paths]\nwork_root="relocated_work"\n')
        self.initialize()
        relocated = json.loads(self.profile.read_text(encoding="utf-8"))
        self.profile.unlink()
        (self.work / "source.bin").unlink()
        self.work.rename(self.root / "_work")
        self.configure('schema_version=1\n[paths]\nwork_root="_work"\n')
        self.initialize()
        self.assertEqual(json.loads(self.profile.read_text(encoding="utf-8")), relocated)

    def test_missing_work_root_is_not_silently_defaulted(self):
        self.configure("schema_version=1\n")
        with self.assertRaises(pc.ConfigError):
            self.initialize()

    def test_declared_locations_cannot_escape(self):
        self.configure('schema_version=1\n[paths]\nwork_root="relocated_work"\n')
        for declared in ("_work/../archive.mem", "_work/.. /archive.mem"):
            with self.subTest(declared=declared):
                with self.assertRaisesRegex(ValueError, "project-relative|escape the project"):
                    self.initialize(source_archive=declared)

    def test_explicit_absolute_location_is_recorded_verbatim(self):
        self.configure('schema_version=1\n[paths]\nwork_root="relocated_work"\n')
        self.initialize(runtime=str(self.work / "runtime.bin"))
        document = json.loads(self.profile.read_text(encoding="utf-8"))
        self.assertEqual(document["reference_runtime"], (self.work / "runtime.bin").as_posix())

    def test_cli_initializes_with_configured_work_root(self):
        self.configure('schema_version=1\n[paths]\nwork_root="relocated_work"\n')
        code = workflow.main(["init-profile", "--project", str(self.root), "--profile", str(self.profile),
                              "--character", "alpha", "--source-archive", "_work/archive.mem",
                              "--source-list", "_work/source.bin", "--runtime", "_work/runtime.bin",
                              "--catalog", "_work/catalog.json"])
        self.assertEqual(code, 0)
        self.assertTrue(self.profile.is_file())
        self.assertFalse((self.root / "_work").exists())


class CacheDestinationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / "relocated_work"
        self.work.mkdir(parents=True)
        (self.root / "config").mkdir()
        (self.root / "config" / "project.toml").write_text(
            'schema_version=1\n[paths]\nwork_root="relocated_work"\n[inputs]\n'
            'bag1_reference_runtime="relocated_work/runtime.bin"\n', encoding="utf-8")
        (self.work / "source.bin").write_bytes(animation())
        (self.work / "runtime.bin").write_bytes(b"runtime")
        (self.work / "rom.bin").write_bytes(b"base game")
        (self.work / "video.bin").write_bytes(b"reference frames")
        catalog = {"schema": 1, "games": {"game": {"inputs": [
            {"file": "_work/rom.bin", "sha256": sha(self.work / "rom.bin")}]}}}
        (self.work / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
        self.profile = self.root / "alpha.json"
        self.profile.write_text(json.dumps({
            "schema": 1, "character": "alpha", "stage": "inventory",
            "source_animation_list": "_work/source.bin", "game_catalog": "_work/catalog.json",
            "reference_runtime": "_work/runtime.bin", "assets": {}, "exceptions": [],
            "exception_assessment": "pending", "validation_evidence": []}), encoding="utf-8")
        self.cache = self.root / "alpha.cache.json"

    def test_legacy_cache_file_is_not_overwritten(self):
        legacy = {"character": "alpha", "catalog": {"source": "somewhere"}, "runtime": {"exefile": "x"}}
        self.cache.write_text(json.dumps(legacy), encoding="utf-8")
        before = sha(self.cache)
        with self.assertRaisesRegex(ValueError, "Refusing to overwrite a non-cache JSON file"):
            workflow.record_cache(self.profile, self.root, self.cache, [self.work / "video.bin"])
        self.assertEqual(sha(self.cache), before)

    def test_cache_destination_is_explicit_and_reloads_inputs(self):
        result = workflow.record_cache(self.profile, self.root, self.cache, [self.work / "video.bin"])
        self.assertEqual(result["status"], "recorded")
        self.assertEqual(workflow.check_cache(self.profile, self.root, self.cache)["status"], "hit")
        (self.work / "runtime.bin").write_bytes(b"other runtime")
        self.assertEqual(workflow.check_cache(self.profile, self.root, self.cache)["status"], "miss")


if __name__ == "__main__":
    unittest.main()
