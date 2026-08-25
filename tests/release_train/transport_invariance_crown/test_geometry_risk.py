import unittest
from scripts.release_train.transport_invariance_crown import Population, Observation, importance_weights, population_geometry, estimate_risk

class GeometryRiskCourt(unittest.TestCase):
    def test_geometry_weights_and_estimators_remain_distinct(self):
        src=Population.from_mapping({'a':8,'b':2}); dst=Population.from_mapping({'a':5,'b':5})
        g=population_geometry(src,dst); self.assertGreater(g.total_variation,0); self.assertGreater(g.hellinger,0)
        w=importance_weights(src,dst,2.0); self.assertGreater(w.ess,0); self.assertLessEqual(w.maximum,2.0)
        obs=(Observation('a',0.1,1.0),Observation('b',0.9,0.5))
        r=estimate_risk(obs,dict(w.weights)); self.assertGreaterEqual(r.upper,r.lower); self.assertGreater(r.disagreement,0)
