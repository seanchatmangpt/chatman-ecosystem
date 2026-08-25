import unittest
from datetime import datetime, timezone
from scripts.develop_train.process_intelligence_substrate import Event, Subject, canonical_trace, object_centric, shared_identity
from scripts.develop_train.process_intelligence_substrate.errors import Refused

class IdentityViewsTest(unittest.TestCase):
    def test_exact_subject_and_event_object_correspondence(self):
        s = Subject.parse("seanchatmangpt/chatman-ecosystem@" + "a" * 40)
        self.assertEqual(s.sha, "a" * 40)
        events = canonical_trace([
            Event("e2", "B", datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc), ("o1",)),
            Event("e1", "A", datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc), ("o1", "o2")),
        ])
        self.assertTrue(shared_identity(events, object_centric(events)))
        with self.assertRaises(Refused):
            Subject.parse("seanchatmangpt/chatman-ecosystem@abc")

if __name__ == "__main__": unittest.main()
