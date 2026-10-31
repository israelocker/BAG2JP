"""Regression checks against original animation meaning and required BAG2 events."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/bag1import'))
from animlib import anim_list,info,info_off
from anim_remap import build,fix_events
class AnimationPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=anim_list((ROOT/'_work/bag1_assets/heat/PLAYER2_P_HEATA2/001.bin').read_bytes())
        cls.result,cls.mapping=build(cls.source);cls.result=anim_list(cls.result)
    def test_tired_is_original_tired_not_caught(self):self.assertEqual(self.mapping[78],69)
    def test_defenses_are_not_hit_reactions(self):
        self.assertEqual(self.mapping[76],65);self.assertEqual(self.mapping[77],64)
    def test_defense_effects_survive(self):
        for slot,effect in ((76,902),(77,903)):
            self.assertIn((1,1,effect),info(self.result[slot])[1])
            self.assertFalse(any(t==16 for t,f,v in info(self.result[slot])[1]))
    def test_defense_callbacks_come_from_stock(self):
        stock=anim_list((ROOT/'assets/archive/characters/heat/model_a_p1/001.bin').read_bytes())
        for slot,effect in ((76,902),(77,903)):
            self.assertIn((1,1,effect),info(stock[slot])[1])
    def test_poses_hold_without_walking(self):
        for slot,source in ((67,64),(68,60)):
            self.assertEqual(self.mapping[slot],source)
            self.assertEqual(self.result[slot][info_off(self.result[slot])+5],1)
    def test_misses_are_explicit_reactions_not_tired(self):
        self.assertEqual([self.mapping[s] for s in range(79,85)],[66,67,68,66,67,68])
    def test_alternate_follows_original_predecessor_dispatch(self):
        self.assertEqual(self.mapping[11],31)
        self.assertEqual(self.mapping[20],19)
    def test_motion_prefixes_and_attack_launch_are_preserved(self):
        for slot in (67,68,76,77,78,79,80,81,82,83,84):
            original=self.source[self.mapping[slot]];converted=self.result[slot]
            self.assertEqual(original[:info_off(original)],converted[:info_off(converted)])
        self.assertIn((16,29,0),info(self.result[74])[1])
if __name__=='__main__':unittest.main()
