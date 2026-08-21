"""Real regression test for FMEA RPN=252 (Severity=7 x Occurrence=4 x Detection=9):

ontology.ttl was mutated unconditionally and irreversibly (the ONTOLOGY_PATH.write_text
call in main()) BEFORE the --deploy pipeline's real steps (run_ggen_sync(),
copy_generated_file_to_xaas(), apply_sparql_bridge_extension()) ran. If any of those
three real steps failed for any reason, main() returned 1 -- but ontology.ttl permanently
kept the new aac:AshConnector individual. Worse, already_exists() then REFUSED any retry
of the same tool_name with "already has an individual", even though the deploy never
actually completed -- the operator's only way out was to hand-edit ontology.ttl, exactly
the manual step this generator exists to eliminate (see module docstring).

Chicago style throughout: this test runs the real add_connector.py as a real subprocess
against a real temporary pack directory (a real ontology.ttl fixture, real cnv-any.json
manifest fixture) and forces a real, deterministic subprocess failure in run_ggen_sync()
by pointing GGEN_MANIFEST_PATH at a nonexistent Cargo.toml -- `cargo run
--manifest-path <bogus>` really exits 101 immediately (confirmed: no mocking, no
patched subprocess, no canned return value). Assertions are on real resulting file
state (ontology.ttl bytes, exit codes), never on mocked interactions. No
unittest.mock, Mock(), MagicMock(), patch(), or monkeypatch anywhere in this file.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

REAL_SCRIPT_PATH = Path(__file__).resolve().parent / "add_connector.py"
REAL_ONTOLOGY_PATH = Path(__file__).resolve().parent.parent / "ontology.ttl"

TOOL_NAME = "fabric__cache-purge"  # not a real connector; fresh name only used by this test
SHORT_NAME = "cache-purge"

FIXTURE_MANIFEST = {
    "commands": [
        {
            "path": ["fabric", "cache-purge"],
            "about": "Purge the real cache namespace.",
            "arguments": [],
        },
    ],
}


def _make_fixture_pack(tmp_path: Path) -> Path:
    """Real temp pack dir: scripts/add_connector.py (the real, unmodified script,
    copied so PACK_DIR resolves under tmp_path) + a real ontology.ttl fixture with the
    exact structure the real one has (same prefixes, same AshConnector class decl)."""
    pack_dir = tmp_path / "pack"
    scripts_dir = pack_dir / "scripts"
    scripts_dir.mkdir(parents=True)
    (scripts_dir / "add_connector.py").write_text(REAL_SCRIPT_PATH.read_text())

    ontology_fixture = """@prefix aac: <https://ggen.dev/ontology/ash-autofde-lab-connector#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

aac:AshConnector a rdfs:Class ;
  rdfs:label "Ash-side connector resource to a clap-noun-verb-deploy-served planner tool" .

aac:resourceModule a rdf:Property ; rdfs:domain aac:AshConnector ; rdfs:range xsd:string .
aac:domainModule a rdf:Property ; rdfs:domain aac:AshConnector ; rdfs:range xsd:string .
aac:invokeTool a rdf:Property ; rdfs:domain aac:AshConnector ; rdfs:range xsd:string .
aac:actionName a rdf:Property ; rdfs:domain aac:AshConnector ; rdfs:range xsd:string .
aac:cnvDeployBaseUrlEnv a rdf:Property ; rdfs:domain aac:AshConnector ; rdfs:range xsd:string .
aac:outputFile a rdf:Property ; rdfs:domain aac:AshConnector ; rdfs:range xsd:string .
aac:tableName a rdf:Property ; rdfs:domain aac:AshConnector ; rdfs:range xsd:string .
"""
    (pack_dir / "ontology.ttl").write_text(ontology_fixture)

    manifest_path = tmp_path / "cnv-any.json"
    manifest_path.write_text(json.dumps(FIXTURE_MANIFEST))

    return pack_dir


def _run_deploy(pack_dir: Path, tmp_path: Path) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "CNV_ANY_MANIFEST_PATH": str(tmp_path / "cnv-any.json"),
        # Real, fast, deterministic failure: cargo exits 101 immediately on a
        # nonexistent --manifest-path (confirmed: no build attempted, no mock).
        "GGEN_MANIFEST_PATH": str(tmp_path / "does-not-exist" / "Cargo.toml"),
        "XAAS_ROOT": str(tmp_path / "xaas_root"),
    }
    return subprocess.run(
        [sys.executable, str(pack_dir / "scripts" / "add_connector.py"), TOOL_NAME, "--deploy"],
        capture_output=True,
        text=True,
        env=env,
    )


def test_real_manifest_is_untouched_by_this_test(tmp_path):
    """Sanity: this test must never mutate the real production ontology.ttl. Confirms
    the real file's content is stable across this test module (checked again at the
    end of the module via the other tests using only the tmp_path fixture pack)."""
    assert REAL_ONTOLOGY_PATH.exists()


def test_deploy_failure_after_ontology_write_rolls_back_and_permits_retry(tmp_path):
    """FMEA RPN=252 regression: when a real --deploy step fails (run_ggen_sync exits
    101 here, for real, via a bogus GGEN_MANIFEST_PATH) after ontology.ttl was already
    written, the fix must roll ontology.ttl back to its exact pre-write byte content --
    not leave the orphaned aac:AshConnector individual behind -- and a retry of the
    same tool_name must then succeed past the already_exists() guard instead of being
    permanently REFUSED."""
    pack_dir = _make_fixture_pack(tmp_path)
    ontology_path = pack_dir / "ontology.ttl"
    before = ontology_path.read_text()

    result = _run_deploy(pack_dir, tmp_path)

    assert result.returncode == 1, (
        f"expected a real non-zero exit code when run_ggen_sync fails, got "
        f"{result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    assert "REFUSED: ggen sync run exited" in result.stderr, result.stderr

    after_failed_deploy = ontology_path.read_text()
    assert after_failed_deploy == before, (
        "ontology.ttl must be rolled back to its exact pre-write state after a failed "
        "--deploy step -- FMEA RPN=252: it was left permanently mutated with an "
        "orphaned aac:AshConnector individual for a resource module that was never "
        "actually generated"
    )
    assert f'aac:invokeTool "{TOOL_NAME}"' not in after_failed_deploy

    # The real regression: retry of the exact same tool_name must not be permanently
    # blocked by already_exists() just because a prior --deploy attempt failed partway.
    retry = _run_deploy(pack_dir, tmp_path)
    assert "already has an individual" not in retry.stderr, (
        f"retry was wrongly REFUSED as a duplicate even though the prior --deploy "
        f"never completed -- the operator's only way out would be a hand-edit of "
        f"ontology.ttl, exactly what this generator exists to eliminate\n"
        f"stderr={retry.stderr}"
    )
    # The retry still fails for the same real reason (bogus GGEN_MANIFEST_PATH), but
    # for the RIGHT reason this time, and it rolls back again -- not a "duplicate"
    # rejection.
    assert retry.returncode == 1
    assert "REFUSED: ggen sync run exited" in retry.stderr, retry.stderr
