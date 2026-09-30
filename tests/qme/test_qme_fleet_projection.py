import copy, importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).parents[2]
spec=importlib.util.spec_from_file_location("qme_fleet_projection",ROOT/"conformance"/"qme-1"/"qme_fleet_projection.py")
qme=importlib.util.module_from_spec(spec); spec.loader.exec_module(qme)
OBS=ROOT/"observations"/"fleet"/"2026-09-30-seven-day.json"; PROJ=ROOT/"conformance"/"qme-1"/"fleet-projection-v26.9.30.json"
def load(): return json.loads(OBS.read_text()),json.loads(PROJ.read_text())
class QMEFleetProjectionTests(unittest.TestCase):
    def refused(self,o,p,code):
        with self.assertRaises(qme.Refusal) as cm:qme.check(o,p)
        self.assertEqual(cm.exception.code,code)
    def test_positive(self):
        o,p=load(); a=qme.check(o,p); b=qme.check(copy.deepcopy(o),copy.deepcopy(p))
        self.assertEqual(a,b); self.assertEqual(a["repository_count"],101); self.assertEqual(a["authority"],"NONE")
    def test_source_authority(self):
        o,p=load(); o["authority"]="DO"; self.refused(o,p,"SOURCE_AUTHORITY_PROMOTION")
    def test_source_standing(self):
        o,p=load(); o["standing"]="ADMITTED"; self.refused(o,p,"SOURCE_STANDING_PROMOTION")
    def test_ggen_read_only(self):
        o,p=load()
        for r in o["repositories"]:
            if r["repository"]=="seanchatmangpt/ggen": r["read_only"]=False
        self.refused(o,p,"GGEN_WRITE_PROMOTION")
    def test_projection_authority(self):
        o,p=load(); p["capability_sets"][0]["authority_effect"]="DO"; self.refused(o,p,"PROJECTION_AUTHORITY_PROMOTION")
    def test_unobserved_capability(self):
        o,p=load(); p["capability_sets"][0]["members"].append("seanchatmangpt/not-observed"); self.refused(o,p,"UNOBSERVED_CAPABILITY")
    def test_equation_drift(self):
        o,p=load(); p["canonical_equation"]="A = model(O)"; self.refused(o,p,"EQUATION_DRIFT")
if __name__=="__main__": unittest.main()
