"""CE23-7 version fence: Chatman tools target an explicit release line, never a literal one.

Chicago style: every tool runs as a real subprocess against real release directories
built in temporary trees from the committed v26.9.1 inputs; resolver functions are
called in-process on real paths. The survey's GitHub collaborator is a local stdlib HTTP
server on 127.0.0.1 because the real one is a remote network service; the survey's own
HTTP client runs unmodified against it.
"""

from __future__ import annotations

import http.server
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import tomllib
import unittest
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PRED, TARGET = "v26.9.1", "v26.9.23"

SPEC = importlib.util.spec_from_file_location("release_line", SCRIPTS / "release_line.py")
assert SPEC is not None and SPEC.loader is not None
release_line = importlib.util.module_from_spec(SPEC)
sys.modules["release_line"] = release_line
SPEC.loader.exec_module(release_line)


def run(script: str, *args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args], cwd=cwd, capture_output=True, text=True, timeout=300
    )


def pointer_line() -> str:
    policy = tomllib.loads((ROOT / "catalog/west.toml").read_text(encoding="utf-8"))
    return Path(policy["boundaries"]["release_manifest"]).parent.name


def write_line(root: Path, line: str, names=("manifest.toml", "fleet-policy.toml", "fanout-bootstrap.toml",
                                              "constitutional-role-crosswalk.toml"), version: str | None = None) -> Path:
    """Copy the v26.9.1 inputs into root/release/<line>/, declaring ``version`` (default: the line's)."""
    version = version if version is not None else line[1:]
    target = root / "release" / line
    target.mkdir(parents=True, exist_ok=True)
    for name in names:
        text = (ROOT / "release" / PRED / name).read_text(encoding="utf-8")
        text = re.sub(r'(?m)^version = "26\.9\.1"$', f'version = "{version}"', text, count=1)
        text = re.sub(r'(?m)^release = "26\.9\.1"$', f'release = "{version}"', text, count=1)
        (target / name).write_text(text, encoding="utf-8")
    return target


def write_catalog(root: Path, manifest: str | None) -> None:
    text = (ROOT / "catalog/west.toml").read_text(encoding="utf-8")
    if manifest is None:
        text = re.sub(r'(?m)^release_manifest = ".*"\n', "", text, count=1)
    else:
        text = re.sub(r'(?m)^release_manifest = ".*"$', f'release_manifest = "{manifest}"', text, count=1)
    (root / "catalog").mkdir(parents=True, exist_ok=True)
    (root / "catalog/west.toml").write_text(text, encoding="utf-8")


class ReleaseLineResolverTests(unittest.TestCase):
    def test_default_is_the_declared_pointer_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for line in (TARGET, PRED):
                write_catalog(root, f"release/{line}/manifest.toml")
                proc = run("release_line.py", "--root", str(root))
                self.assertEqual((0, f"release/{line}\n"), (proc.returncode, proc.stdout), proc.stderr)

    def test_explicit_release_is_canonicalized(self) -> None:
        for value in ("v26.9.23", "v26.09.23", "26.9.23"):
            proc = run("release_line.py", "--release", value)
            self.assertEqual((0, "release/v26.9.23\n"), (proc.returncode, proc.stdout), value)

    def test_invalid_release_is_refused_typed(self) -> None:
        for value in ("v26.13.1", "v26.2.30", "latest", "v2026.9.23"):
            proc = run("release_line.py", "--release", value)
            self.assertEqual(2, proc.returncode, value)
            self.assertIn(f"RELEASE_LINE_INVALID:{value}", proc.stderr)

    def test_missing_pointer_is_refused_typed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            write_catalog(Path(tmp), None)
            proc = run("release_line.py", "--root", tmp)
            self.assertEqual(2, proc.returncode)
            self.assertIn("RELEASE_POINTER_MISSING:catalog/west.toml", proc.stderr)

    def test_version_is_bound_only_by_a_canonical_release_directory(self) -> None:
        cases = {
            "release/v26.9.23/manifest.toml": "26.9.23",
            "/tmp/x/release/v26.9.1/manifest.toml": "26.9.1",
            "release/v26.09.23/manifest.toml": None,
            "release/26.9.23/manifest.toml": None,
            "archive/v26.9.23/manifest.toml": None,
            "manifest.toml": None,
        }
        for path, expected in cases.items():
            self.assertEqual(expected, release_line.version_from_path(Path(path)), path)

    def test_explicit_inputs_are_bound_to_the_requested_line(self) -> None:
        pred = Path(f"release/{PRED}/manifest.toml")
        with self.assertRaisesRegex(release_line.ReleaseLineError, "^RELEASE_TARGET_CONFLICT:"):
            release_line.bind(pred, TARGET)
        with self.assertRaisesRegex(release_line.ReleaseLineError, "^RELEASE_TARGET_UNBOUND:"):
            release_line.bind(Path("/tmp/manifest.toml"), TARGET)
        self.assertEqual(pred, release_line.bind(pred, PRED))
        target = Path(f"release/{TARGET}/manifest.toml")
        self.assertEqual(Path(f"release/{TARGET}/fleet-policy.toml"), release_line.companion(target, "fleet-policy.toml"))
        with self.assertRaisesRegex(release_line.ReleaseLineError, "^RELEASE_TARGET_CONFLICT:.*manifest to v26.9.23"):
            release_line.companion(target, "fleet-policy.toml", Path(f"release/{PRED}/fleet-policy.toml"))


class VerifyReleaseVersionLawTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def report(self, *args: str) -> tuple[int, dict]:
        proc = run("verify_release.py", *args, cwd=self.root)
        return proc.returncode, json.loads(proc.stdout)

    def test_target_manifest_declaring_its_line_is_admitted(self) -> None:
        manifest = write_line(self.root, TARGET, ("manifest.toml",)) / "manifest.toml"
        code, report = self.report("--manifest", str(manifest))
        self.assertEqual((0, "26.9.23", []), (code, report["release"], report["findings"]))
        self.assertEqual((0, report), self.report("--release", TARGET))

    def test_predecessor_manifest_under_target_directory_is_refused(self) -> None:
        manifest = write_line(self.root, TARGET, ("manifest.toml",), version="26.9.1") / "manifest.toml"
        code, report = self.report("--manifest", str(manifest))
        self.assertEqual(2, code)
        self.assertIn(
            {"code": "ECOSYSTEM_VERSION_MISMATCH", "subject": "release.version", "detail": "VERSION_PATH_MISMATCH: expected 26.9.23"},
            report["findings"],
        )

    def test_unbound_and_invalid_versions_are_refused(self) -> None:
        loose = self.root / "loose"
        loose.mkdir()
        shutil.copy2(ROOT / "release" / PRED / "manifest.toml", loose / "manifest.toml")
        code, report = self.report("--manifest", str(loose / "manifest.toml"))
        self.assertEqual((2, ["ECOSYSTEM_VERSION_PATH_UNBOUND"]), (code, [f["code"] for f in report["findings"]]))
        manifest = write_line(self.root, TARGET, ("manifest.toml",), version="v26.9.23") / "manifest.toml"
        code, report = self.report("--manifest", str(manifest))
        self.assertEqual((2, ["ECOSYSTEM_VERSION_INVALID"]), (code, [f["code"] for f in report["findings"]]))

    def test_release_flag_conflicting_with_manifest_is_refused(self) -> None:
        write_line(self.root, PRED, ("manifest.toml",))
        write_line(self.root, TARGET, ("manifest.toml",))
        proc = run("verify_release.py", "--release", TARGET, "--manifest", f"release/{PRED}/manifest.toml", cwd=self.root)
        self.assertEqual(2, proc.returncode)
        self.assertIn("RELEASE_TARGET_CONFLICT:release/v26.9.1/manifest.toml is bound to v26.9.1, --release is v26.9.23", proc.stderr)

    def test_missing_target_line_is_refused_typed(self) -> None:
        proc = run("verify_release.py", "--release", "v26.9.30", cwd=self.root)
        self.assertEqual(2, proc.returncode)
        self.assertIn("RELEASE_INPUT_MISSING:release/v26.9.30/manifest.toml", proc.stderr)


class PlannerLineTests(unittest.TestCase):
    def test_planner_branches_carry_the_target_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            write_line(Path(tmp), TARGET)
            proc = run("plan_completion.py", "--release", TARGET, cwd=Path(tmp))
            self.assertEqual(0, proc.returncode, proc.stderr)
            plan = json.loads(proc.stdout)
            branches = [packet["branch"] for packet in plan["packets"] if packet["branch"]]
            self.assertEqual("26.9.23", plan["release"])
            self.assertTrue(branches)
            self.assertEqual([], [branch for branch in branches if not branch.startswith("agent/v26.9.23-")])

    def test_planner_refuses_a_cross_line_companion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            write_line(Path(tmp), TARGET)
            write_line(Path(tmp), PRED)
            proc = run("plan_completion.py", "--manifest", f"release/{TARGET}/manifest.toml",
                       "--fleet", f"release/{PRED}/fleet-policy.toml", cwd=Path(tmp))
            self.assertEqual(2, proc.returncode)
            self.assertIn("RELEASE_TARGET_CONFLICT:release/v26.9.1/fleet-policy.toml is bound to v26.9.1, the manifest to v26.9.23", proc.stderr)

    def test_planner_default_is_the_explicit_pointer_line(self) -> None:
        default, explicit = run("plan_completion.py"), run("plan_completion.py", "--release", pointer_line())
        self.assertEqual((0, default.stdout), (explicit.returncode, explicit.stdout))


class _GitHub(http.server.BaseHTTPRequestHandler):
    repos: list[dict] = []

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - BaseHTTPRequestHandler signature
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/users/"):
            body = self.repos if urllib.parse.parse_qs(parsed.query).get("page") == ["1"] else []
        elif parsed.path == "/search/issues":
            body = {"total_count": 0, "items": []}
        else:
            self.send_response(404)
            self.end_headers()
            return
        payload = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class SurveyLineTests(unittest.TestCase):
    def test_survey_scope_and_report_follow_the_target_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = tomllib.loads((write_line(root, TARGET) / "manifest.toml").read_text(encoding="utf-8"))
            repo = next(c["repository"] for c in manifest["components"] if c["repository"].startswith("seanchatmangpt/"))
            _GitHub.repos = [{"full_name": repo, "owner": {"login": "seanchatmangpt"}, "private": False}]
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _GitHub)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                proc = run("survey_portfolio.py", "--release", TARGET, "--api-url", f"http://127.0.0.1:{server.server_address[1]}",
                           "--observed-at", "2026-09-23T00:00:00Z", "--output-dir", str(root / "out"), cwd=root)
            finally:
                server.shutdown()
                server.server_close()
            self.assertEqual(0, proc.returncode, proc.stderr)
            self.assertIn("- v26.9.23 required components:", (root / "out/REPORT.md").read_text(encoding="utf-8"))
            census = (root / "out/REPO_CENSUS.csv").read_text(encoding="utf-8")
            self.assertIn(f"{repo},", census)
            self.assertIn("REQUIRED_V26_9_23", census)
            self.assertNotIn("V26_9_1", census)

    def test_survey_companion_inputs_come_from_the_manifest_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            write_line(Path(tmp), TARGET, ("manifest.toml",))
            write_line(Path(tmp), PRED)
            proc = run("survey_portfolio.py", "--release", TARGET, "--output-dir", str(Path(tmp) / "out"), cwd=Path(tmp))
            self.assertEqual(2, proc.returncode)
            self.assertIn("RELEASE_INPUT_MISSING:release/v26.9.23/fleet-policy.toml", proc.stderr)


class StandingAndWestLineTests(unittest.TestCase):
    def test_standing_verifier_targets_an_explicit_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            write_line(Path(tmp), TARGET, ("manifest.toml",))
            write_line(Path(tmp), PRED, ("manifest.toml",))
            target = run("verify_standing_evidence.py", "--release", TARGET, cwd=Path(tmp))
            self.assertEqual(0, target.returncode, target.stderr)
            self.assertEqual("chatman-ecosystem.standing-evidence/1", json.loads(target.stdout)["schema"])
            conflict = run("verify_standing_evidence.py", "--release", TARGET, "--manifest", f"release/{PRED}/manifest.toml", cwd=Path(tmp))
            self.assertEqual(2, conflict.returncode)
            self.assertIn("RELEASE_TARGET_CONFLICT", conflict.stderr)
        default, explicit = run("verify_standing_evidence.py"), run("verify_standing_evidence.py", "--release", pointer_line())
        self.assertEqual((default.returncode, default.stdout), (explicit.returncode, explicit.stdout))

    def test_west_refuses_a_projection_sourced_from_another_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("catalog", "west"):
                shutil.copytree(ROOT / name, root / name)
            for name in ("west.yml", ".gitmodules"):
                shutil.copy2(ROOT / name, root / name)
            write_line(root, TARGET, ("manifest.toml",))
            write_catalog(root, f"release/{TARGET}/manifest.toml")
            west = ["verify_west_workspace.py", "--json", "--root", str(root)]
            refused = run(*west, cwd=root)
            self.assertEqual(1, refused.returncode)
            self.assertIn("REFUSED:WEST_RELEASE_SOURCE_MISMATCH:release/v26.9.23/manifest.toml:", refused.stderr)
            projection = (root / "west.yml").read_text(encoding="utf-8")
            (root / "west.yml").write_text(projection.replace(f"source: release/{PRED}/", f"source: release/{TARGET}/"), encoding="utf-8")
            admitted = run(*west, cwd=root)
            self.assertEqual(0, admitted.returncode, admitted.stderr)
            explicit = run(*west, "--release", TARGET, cwd=root)
            self.assertEqual((admitted.returncode, admitted.stdout), (explicit.returncode, explicit.stdout))
            conflict = run(*west, "--release", TARGET, "--release-manifest", f"release/{PRED}/manifest.toml", cwd=root)
            self.assertEqual(2, conflict.returncode)
            self.assertIn("RELEASE_TARGET_CONFLICT", conflict.stderr)

    def test_west_default_is_the_explicit_pointer_line(self) -> None:
        default = run("verify_west_workspace.py", "--json")
        explicit = run("verify_west_workspace.py", "--json", "--release", pointer_line())
        self.assertEqual((default.returncode, default.stdout), (explicit.returncode, explicit.stdout))


if __name__ == "__main__":
    unittest.main()
