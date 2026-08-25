import unittest
from scripts.release_train.transport_invariance_crown import Population, Refused, Subject, admit_support

class SubjectSupportCourt(unittest.TestCase):
    def test_exact_subject_and_positivity(self):
        s=Subject('seanchatmangpt/chatman-ecosystem','a'*40,'b'*64)
        self.assertIn('@',s.identity)
        src=Population.from_mapping({'a':9,'b':1}); dst=Population.from_mapping({'a':8,'b':2})
        w=admit_support(src,dst); self.assertEqual(w.supported_cells,2)
        with self.assertRaisesRegex(Refused,'POSITIVITY_VIOLATION'):
            admit_support(Population.from_mapping({'a':1}),Population.from_mapping({'a':1,'b':1}))
        with self.assertRaisesRegex(Refused,'INVALID_SHA'):
            Subject('o/r','bad','b'*64)
