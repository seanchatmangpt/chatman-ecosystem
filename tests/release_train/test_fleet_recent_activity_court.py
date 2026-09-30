from __future__ import annotations
import copy,json,sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/"scripts"/"release_train"));import fleet_recent_activity_court as court
SNAP=ROOT/"observations"/"fleet"/"2026-09-30-seven-day.json"
class FleetRecentActivityCourtTests(unittest.TestCase):
    def load(self):return json.loads(SNAP.read_text())
    def test_snapshot(self):
        r,c=court.evaluate(self.load());self.assertEqual(0,c);self.assertEqual("ALIVE",r["standing"]);self.assertEqual(101,r["repository_count"]);self.assertEqual("NONE",r["authority"])
    def test_ggen_read_only(self):
        d=self.load();self.assertTrue(next(x for x in d["repositories"] if x["repository"]=="seanchatmangpt/ggen")["read_only"])
    def test_duplicate_refuses(self):
        d=self.load();d["repositories"].append(copy.deepcopy(d["repositories"][0]));d["repository_count"]+=1;r,c=court.evaluate(d);self.assertEqual(2,c);self.assertIn("REFUSED[DUPLICATE_REPOSITORY]",r["findings"])
    def test_promotion_refuses(self):
        d=self.load();d["repositories"][0]["standing"]="ALIVE";r,c=court.evaluate(d);self.assertEqual(2,c);self.assertTrue(any("ROW_PROMOTION" in x for x in r["findings"]))
    def test_old_timestamp_refuses(self):
        d=self.load();d["repositories"][0]["commit_timestamp"]="2020-01-01T00:00:00Z";r,c=court.evaluate(d);self.assertEqual(2,c);self.assertTrue(any("OUTSIDE_WINDOW" in x for x in r["findings"]))
    def test_ggen_write_flag_refuses(self):
        d=self.load();next(x for x in d["repositories"] if x["repository"]=="seanchatmangpt/ggen")["read_only"]=False;r,c=court.evaluate(d);self.assertEqual(2,c);self.assertIn("REFUSED[GGEN_NOT_READ_ONLY]",r["findings"])
if __name__=="__main__":unittest.main()
