"""CE23-2 lane-spec totality check (scan-plan wave CE lane CE23-2 gate, adapted to the pack's field names).

Re-renders release/v26.9.23 with ggen, requires no diff against the commit, then checks with plain
tomllib (no court code) that out/legacy-role-crosswalk.toml carries exactly the 16
(role, component, sha) triples of release/v26.9.1/manifest.toml, each with one of the five
boundaries, a reason and derived_by/decided_by provenance. The lane spec named the file
release/v26.9.23/legacy-role-crosswalk.toml and a `disposition` field; the vendored pack renders
out/legacy-role-crosswalk.toml with a `boundary` field.
"""
import subprocess
import sys
import tomllib

sync = subprocess.run(["ggen", "sync", "run"], cwd="release/v26.9.23", capture_output=True, text=True)
if sync.returncode != 0:
    sys.exit(f"ggen sync run exit {sync.returncode}")
if subprocess.run(["git", "diff", "--exit-code", "--quiet", "--", "release/v26.9.23"]).returncode != 0:
    sys.exit("render differs from the commit")
x = tomllib.load(open("release/v26.9.23/out/legacy-role-crosswalk.toml", "rb"))
m = tomllib.load(open("release/v26.9.1/manifest.toml", "rb"))
L = {(c["role"], c["id"], c["sha"]) for c in m["components"]}
X = {(r["legacy_role"], r["legacy_component"], r["legacy_sha"]) for r in x["role"]}
assert len(x["role"]) == 16 and X == L, (len(x["role"]), L ^ X)
assert sorted(r["legacy_role"] for r in x["role"]) == sorted(m["release"]["required_roles"])
assert all(r["boundary"] in {"REQUIRED", "SUCCESSOR", "BLOCKED", "UNSUPPORTED", "REFUSED"} for r in x["role"])
assert all(r["reason"] and (r["derived_by"] or r["decided_by"]) for r in x["role"])
print("LANE_SPEC_CHECK OK:", len(x["role"]), "rows =", len(L), "manifest (role, component, sha) triples;",
      sorted({r["boundary"] for r in x["role"]}))
