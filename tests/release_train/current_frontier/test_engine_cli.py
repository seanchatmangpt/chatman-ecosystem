import io, json, unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from scripts.release_train.current_frontier.cli import main
class T(unittest.TestCase):
 def payload(self):
  return {"predecessor":"124aaaca626ff239c97b9a18cc91cd5d525a8c60","evidence":{"lib":[{"id":"l","subject":"o/lib@"+"a"*40,"scope":"REPOSITORY","outcome":"PASS","observed_at":"2026-08-22T10:00:00Z","run_id":"1"}],"app":[{"id":"a","subject":"o/app@"+"b"*40,"scope":"REPOSITORY","outcome":"PASS","observed_at":"2026-08-22T10:00:01Z","run_id":"2"}]},"supersession":{},"obligations":[{"obligation_id":"repo","required_scope":"REPOSITORY","required":True}],"graph":{"lib":[],"app":["lib"]}}
 def invoke(self):
  out=io.StringIO(); data=json.dumps(self.payload())
  with patch("sys.stdin",io.StringIO(data)), redirect_stdout(out): self.assertEqual(main(),0)
  return out.getvalue()
 def test_deterministic_e2e(self):
  one=self.invoke(); two=self.invoke(); self.assertEqual(one,two); decoded=json.loads(one); self.assertEqual(decoded["plan"]["phases"],["VERIFY","CONSTRUCT"]); self.assertFalse(decoded["receipt"]["body"]["actuation_performed"])
