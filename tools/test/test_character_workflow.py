"""Behavioral checks for the shared, character-independent reference workflow."""
import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("character_workflow",Path(__file__).parents[1]/"bag1import/character_workflow.py")
workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(workflow)

def animation(event=0,motion=0):
    data=bytearray(36)
    struct.pack_into("<I",data,0,28);struct.pack_into("<H",data,4,2)
    struct.pack_into("<I",data,28,4);data[8]=motion;data[32]=event
    return struct.pack("<I",len(data))+data+bytes(4)

def configure_runtime(root):
    config = root / "config"
    config.mkdir(exist_ok=True)
    (config / "project.toml").write_text('schema_version=1\n[inputs]\nbag1_reference_runtime="runtime.bin"\n')

class ReferenceCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        configure_runtime(self.root)
        (self.root/"source.bin").write_bytes(animation())
        (self.root/"runtime.bin").write_bytes(b"runtime")
        (self.root/"rom.bin").write_bytes(b"base game")
        (self.root/"video.bin").write_bytes(b"reference frames")
        self.catalog={"schema":1,"games":{"game":{"inputs":[{"file":"rom.bin","sha256":workflow.file_sha(self.root/"rom.bin")}]}}}
        (self.root/"catalog.json").write_text(json.dumps(self.catalog))
        self.profile=self.root/"profile.json";self.cache=self.root/"cache.json"
        self.data={"schema":1,"character":"alpha","stage":"inventory","source_animation_list":"source.bin",
                   "reference_runtime":"runtime.bin","game_catalog":"catalog.json","exceptions":[]}
        self.save_profile()
    def save_profile(self):
        self.profile.write_text(json.dumps(self.data))
    def record(self):
        workflow.record_cache(self.profile,self.root,self.cache,[self.root/"video.bin"])
    def check(self):
        return workflow.check_cache(self.profile,self.root,self.cache)["status"]
    def test_unchanged_reference_hits(self):
        self.record();self.assertEqual(self.check(),"hit")
    def test_event_only_change_keeps_visual_reference(self):
        self.record();(self.root/"source.bin").write_bytes(animation(event=7))
        self.assertEqual(self.check(),"hit")
    def test_nonvisual_profile_change_keeps_visual_reference(self):
        self.record();self.data["capabilities"]={"ending":True};self.save_profile()
        self.assertEqual(self.check(),"hit")
    def test_motion_change_invalidates_reference(self):
        self.record();(self.root/"source.bin").write_bytes(animation(motion=7))
        self.assertEqual(self.check(),"miss")
    def test_second_character_is_separate(self):
        self.record();self.data["character"]="beta";self.save_profile()
        self.assertEqual(self.check(),"miss")
        self.record();self.assertEqual(self.check(),"hit")
    def test_evidence_tampering_invalidates(self):
        self.record();(self.root/"video.bin").write_bytes(b"other frames")
        self.assertEqual(self.check(),"miss")
    def test_runtime_change_invalidates(self):
        self.record();(self.root/"runtime.bin").write_bytes(b"new runtime")
        self.assertEqual(self.check(),"miss")
    def test_catalog_drift_is_rejected(self):
        self.record();(self.root/"rom.bin").write_bytes(b"other game")
        with self.assertRaises(ValueError):self.check()
    def test_pending_exception_prevents_verified_stage(self):
        self.data.update(stage="verified",validation_evidence=[{"file":"video.bin","sha256":workflow.file_sha(self.root/"video.bin")}],
                         exceptions=[{"id":"special-bone","character":"alpha","reason":"observed binding","status":"pending"}])
        self.save_profile()
        with self.assertRaises(ValueError):workflow.load_profile(self.profile,self.root)
    def test_exception_cannot_leak_to_other_character(self):
        self.data["exceptions"]=[{"id":"special-bone","character":"beta","reason":"observed binding","status":"pending"}]
        self.save_profile()
        with self.assertRaises(ValueError):workflow.load_profile(self.profile,self.root)
    def test_truncated_animation_is_rejected(self):
        (self.root/"source.bin").write_bytes(struct.pack("<I",999)+b"bad")
        with self.assertRaises(ValueError):workflow.motion_fingerprint(self.root/"source.bin")
    def model_archive(self):
        motion=animation()
        payload=struct.pack("<4sI4I",b"DFS_",2,24,4,28,len(motion))+bytes(4)+motion
        archive=self.root/"model.dfs";archive.write_bytes(payload)
        return archive
    def test_init_profile_is_shared_across_characters(self):
        archive=self.model_archive()
        for name in ("gamma","delta"):
            result=workflow.init_profile(self.root,self.root/(name+".json"),name,archive,name+".bin","runtime.bin","catalog.json")
            self.assertEqual(result["animation_count"],1)
            self.assertFalse(result["generation_ready"])
            profile,pending=workflow.load_profile(self.root/(name+".json"),self.root)
            self.assertEqual(profile["character"],name)
    def test_init_refuses_existing_profile(self):
        with self.assertRaises(ValueError):
            workflow.init_profile(self.root,self.profile,"gamma",self.model_archive(),"gamma.bin","runtime.bin","catalog.json")
    def test_init_refuses_malformed_archive(self):
        archive=self.root/"bad.dfs";archive.write_bytes(b"bad")
        with self.assertRaises(ValueError):
            workflow.init_profile(self.root,self.root/"new.json","gamma",archive,"new.bin","runtime.bin","catalog.json")
        self.assertFalse((self.root/"new.json").exists())
    def test_invalid_animation_leaves_no_outputs(self):
        archive=self.model_archive()
        data=bytearray(archive.read_bytes());struct.pack_into("<I",data,28,999)
        archive.write_bytes(data)
        with self.assertRaises(ValueError):
            workflow.init_profile(self.root,self.root/"new.json","gamma",archive,"new.bin","runtime.bin","catalog.json")
        self.assertFalse((self.root/"new.json").exists())
        self.assertFalse((self.root/"new.bin").exists())
    def test_cache_cannot_overwrite_rom_input(self):
        original=(self.root/"rom.bin").read_bytes()
        with self.assertRaises(ValueError):
            workflow.record_cache(self.profile,self.root,self.root/"rom.bin",[self.root/"video.bin"])
        self.assertEqual((self.root/"rom.bin").read_bytes(),original)
    def test_cache_cannot_overwrite_unrelated_json(self):
        other=self.root/"other.json";other.write_text('{"owner":"user"}')
        with self.assertRaises(ValueError):
            workflow.record_cache(self.profile,self.root,other,[self.root/"video.bin"])
        self.assertEqual(json.loads(other.read_text()),{"owner":"user"})
    def test_cache_cannot_overwrite_catalog(self):
        original=(self.root/"catalog.json").read_bytes()
        with self.assertRaises(ValueError):
            workflow.record_cache(self.profile,self.root,self.root/"catalog.json",[self.root/"video.bin"])
        self.assertEqual((self.root/"catalog.json").read_bytes(),original)

class CharacterPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        configure_runtime(self.root)
        (self.root/"source.bin").write_bytes(animation())
        (self.root/"runtime.bin").write_bytes(b"runtime")
        (self.root/"rom.bin").write_bytes(b"base game")
        catalog={"schema":1,"games":{"game":{"inputs":[{"file":"rom.bin","sha256":workflow.file_sha(self.root/"rom.bin")}]}}}
        (self.root/"catalog.json").write_text(json.dumps(catalog))
        self.profile=self.root/"profile.json"
        self.data=dict(schema=2,character="alpha",display_name="Alpha",source_character_id=3,target_character_id=4,
                      stage="candidate",exception_assessment="complete",
                      source_animation_list="source.bin",reference_runtime="runtime.bin",game_catalog="catalog.json",
                      capabilities={"costumes":["a","b"],"versions":["bag1","bag2"],
                                    "fever":["solo","duet"],"stage":True,"song":True,
                                    "ending":True,"shared_announcer_name":True,"online_content":True},
                      assets={"source_model":{"file":"source.bin","sha256":workflow.file_sha(self.root/"source.bin"),"required":True}})
        self.save_profile()
    def save_profile(self):
        self.profile.write_text(json.dumps(self.data))
    def test_schema2_requires_data_only_profile_sections(self):
        profile,pending=workflow.load_profile(self.profile,self.root)
        self.assertEqual(profile["display_name"],"Alpha");self.assertEqual(pending,[])
    def test_required_asset_hash_drift_is_rejected(self):
        self.data["assets"]["source_model"]["sha256"]="0"*64;self.save_profile()
        with self.assertRaises(ValueError):workflow.load_profile(self.profile,self.root)
    def test_plan_reports_unresolved_character_without_claiming_import(self):
        self.data["target_character_id"]=None;self.data["stage"]="inventory";self.data["exception_assessment"]="pending";self.save_profile()
        plan=workflow.character_plan(self.profile,self.root)
        self.assertIn("target_character_id",plan["gaps"])
        self.assertIn("contract_not_approved",plan["gaps"])
        self.assertFalse(plan["prepare_ready"])
    def test_acceptance_plan_is_capability_driven(self):
        cases={case["id"] for case in workflow.character_plan(self.profile,self.root)["acceptance"]}
        self.assertTrue({"model-sides-costumes","mixed-version","fever-solo","fever-duet",
                          "stage-load","song-end","ending-video-credits-return",
                          "announcer-name","online-content-identity"} <= cases)
    def test_prepare_creates_manifest_but_never_deploys(self):
        self.configure_workspace()
        result=workflow.prepare_workspace(self.profile,self.root)
        manifest=Path(result["manifest"])
        self.assertTrue(manifest.is_file())
        self.assertIn("candidate",manifest.parts)
        self.assertFalse(any(p.name=="BAG2JP.exe" for p in self.root.rglob("*")))
    def test_state_write_is_compact_and_resumable(self):
        self.configure_workspace()
        plan=workflow.character_plan(self.profile,self.root)
        path=workflow.write_state(self.root,plan,"planned")
        state=json.loads(path.read_text())
        self.assertEqual(state["character"],"alpha")
        self.assertEqual(state["next_action"],"prepare")
        self.assertLess(path.stat().st_size,8192)

    def configure_workspace(self):
        config = self.root / "config"; config.mkdir(exist_ok=True)
        (config / "project.toml").write_text('schema_version=1\n[inputs]\nbag1_reference_runtime="runtime.bin"\n[paths]\nwork_root="_work"\nstable_install="stable"\n')

if __name__=="__main__":
    unittest.main()
