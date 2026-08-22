import json, subprocess, sys, unittest
PAYLOAD={"producer":"o/a@"+"a"*40,"event_id":"e","kind":"BUILD_BROKEN","at":"2026-01-01T00:00:00+00:00",
"edges":[["o/a@"+"a"*40,"o/b@"+"b"*40],["o/b@"+"b"*40,"o/c@"+"c"*40]],
"witnesses":[{"consumer":"o/b@"+"b"*40,"state":"DELIVERED","at":"2026-01-01T00:00:01+00:00"},
{"consumer":"o/b@"+"b"*40,"state":"ACKNOWLEDGED","at":"2026-01-01T00:00:02+00:00"},
{"consumer":"o/b@"+"b"*40,"state":"DISCHARGED","result":"REQUALIFIED","at":"2026-01-01T00:00:03+00:00"}],
"strategy":{"kind":"ALL"},"require_durable":True}
class T(unittest.TestCase):
    def test_deterministic_and_incomplete(self):
        cmd=[sys.executable,"-m","scripts.release_train.ack_discharge_promotion.cli"]
        one=subprocess.run(cmd,input=json.dumps(PAYLOAD),text=True,capture_output=True,check=True).stdout
        two=subprocess.run(cmd,input=json.dumps(PAYLOAD),text=True,capture_output=True,check=True).stdout
        self.assertEqual(one,two)
        data=json.loads(one); self.assertEqual(data["standing"],"UNKNOWN"); self.assertFalse(data["receipt"]["body"]["actuation_performed"])
