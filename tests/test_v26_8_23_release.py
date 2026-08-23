import importlib.util,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("verify_release",ROOT/"scripts/verify_v26_8_23.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class T(unittest.TestCase):
 def copy(self):
  td=tempfile.TemporaryDirectory();dst=Path(td.name);shutil.copytree(ROOT/"release",dst/"release");shutil.copytree(ROOT/"scripts",dst/"scripts");shutil.copy(ROOT/"Cargo.toml",dst/"Cargo.toml");return td,dst
 def test_current_capsule(self):
  r=m.verify(ROOT);self.assertEqual(r["status"],"VERIFIED");self.assertFalse(r["body"]["actuation_performed"]);self.assertEqual(r["body"]["version"],"26.8.23")
 def test_wrong_version_refuses(self):
  td,d=self.copy()
  try:
   p=d/"Cargo.toml";p.write_text(p.read_text().replace('version = "26.8.23"','version = "0.1.0"',1))
   with self.assertRaisesRegex(m.ReleaseRefusal,"WORKSPACE_VERSION_MISMATCH"):m.verify(d)
  finally:td.cleanup()
 def test_false_alive_refuses(self):
  td,d=self.copy()
  try:
   p=d/"release/v26.8.23/manifest.toml";p.write_text(p.read_text().replace('standing="PARTIAL_ALIVE"','standing="ALIVE"',1))
   with self.assertRaisesRegex(m.ReleaseRefusal,"FALSE_ALIVE_WITH_OPEN_REQUIREMENTS"):m.verify(d)
  finally:td.cleanup()
 def test_duplicate_requirement_refuses(self):
  td,d=self.copy()
  try:
   p=d/"release/v26.8.23/requirements.toml";p.write_text(p.read_text()+'\n[[requirements]]\nid="R-001";name="dup";category="x";state="UNKNOWN";acceptance="false";depends_on=[]\n')
   with self.assertRaisesRegex(m.ReleaseRefusal,"DUPLICATE_REQUIREMENT_ID"):m.verify(d)
  finally:td.cleanup()
 def test_future_line_is_preserved(self):
  td,d=self.copy()
  try:
   shutil.rmtree(d/"release/v26.9.1")
   with self.assertRaisesRegex(m.ReleaseRefusal,"FUTURE_LINE_NOT_PRESERVED"):m.verify(d)
  finally:td.cleanup()
if __name__=="__main__":unittest.main()
