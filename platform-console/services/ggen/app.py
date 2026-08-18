"""ggen-status service: health/status stub + a real ggen sync provisioning endpoint.

Endpoints:
  GET  /healthz    -> 200 {"status": "ok"}                (k8s liveness probe, unchanged)
  GET  /status     -> 200 <contents of facts.json>         (unchanged, build-time-baked facts)
  POST /provision   -> runs the REAL `ggen` CLI's real sync pipeline via subprocess and
                        returns the real generated artifacts plus the real, independently
                        verifiable BLAKE3-chained signed receipt (`praxis-core::receipt_record`
                        shape, produced by `ggen-engine::sync`).

Why subprocess, not an in-process Python binding
--------------------------------------------------
There is no Python binding for `ggen-engine`/`praxis-core` -- confirmed by the prior
ground-truth survey and by this implementation pass (no PyO3/maturin-built wheel, no FFI
shim in this repo). `ggen-mcp` calls `ggen_engine::sync::sync` in-process, but that is a
Rust-to-Rust crate dependency; it is not reachable from this Python service without adding
a new Rust binary/FFI surface, which is out of scope for this pass. The one real,
already-established cross-language integration pattern in this ecosystem is the
castle -> autofde-lab / gymact subprocess+JSON bridge (`castle.rs` `Command::new(...)`,
`castle_bridge/plan_astar.py`). This service follows that same precedent: shell out to the
real, already-compiled `ggen` binary and parse its real JSON stdout. Nothing here is
simulated -- if the binary is missing or the pipeline fails, the failure is reported
verbatim (stdout/stderr/returncode), never swallowed into a synthesized "ok".

Why `ggen sync run` takes no ontology/pack CLI flags
-----------------------------------------------------
Confirmed directly (`ggen sync run --help`, and by running it in an empty dir): the real
CLI surface is `--dry-run --format --select --watch --introspect --structured-errors
--autonomic` only. The pipeline is driven entirely by a `ggen.toml` manifest at the project
root. So provisioning an ontology means materializing a real project directory (via the
real `ggen init` scaffold) and writing the caller's ontology into it before invoking
`ggen sync run`, not passing the ontology as a flag.

Signing key management
-----------------------
Per the ticket, the caller never supplies or manages a signing key. `ggen-engine::keys`'s
own real precedence is: `GGEN_SIGNING_KEY` env var, else `<project>/.ggen/keys/signing.key`
(generated on first use), never asking the caller. This service adopts the env-var branch
of that same precedence and manages it at the *service* level rather than per-run-directory:
on startup it resolves one signing key -- `GGEN_SIGNING_KEY` if the platform operator has
already injected it (e.g. via a k8s Secret mounted as an env var, following
platform-console's existing Secret conventions), otherwise a local key file at
`SIGNING_KEY_PATH` (default `/app/state/keys/signing.key`), generating a fresh
`secrets.token_hex(32)` seed with `0o600` perms the first time the service boots if neither
is present. That single resolved key is then exported into every `ggen` subprocess's
environment for both `sync run` and `receipt verify`, so every run this service produces is
signed and verifiable with the same platform key, and the caller is never asked for one.
Caveat, stated honestly: this local key file is only as durable as the pod's local
filesystem -- if `/app/state` is not backed by a PersistentVolume, a pod restart mints a new
key and receipts signed under the old key can no longer be verified via a freshly-derived
verifying key from the new `GGEN_SIGNING_KEY`. No PVC exists for this Deployment today;
wiring one (or sourcing the key from a real k8s Secret set up out-of-band) is the correct
production fix and is noted in the ticket doc, not silently worked around here.

Packs
-----
`ggen sync run` has no pack-list flag either. The real, already-existing subcommand for
associating a pack with a project is `ggen packs install --pack-id <id>` (confirmed via
`ggen packs install --help`) -- it is deliberately lenient (a pack unresolved against a
registry is recorded `status: declared` rather than erroring). For each pack name in the
request's `packs` list, this service really runs that subcommand inside the run directory
before `sync run` and reports each real per-pack result (`installed`/`declared`/error)
rather than silently accepting or dropping the list.
"""
import json
import os
import secrets
import shutil
import subprocess
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

FACTS_PATH = os.environ.get("FACTS_PATH", "/app/facts.json")
GGEN_BIN = os.environ.get("GGEN_BIN", "/usr/local/bin/ggen")
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "/app/state/runs"))
SIGNING_KEY_PATH = Path(os.environ.get("SIGNING_KEY_PATH", "/app/state/keys/signing.key"))
SYNC_TIMEOUT_S = int(os.environ.get("GGEN_SYNC_TIMEOUT_S", "120"))

with open(FACTS_PATH, "r", encoding="utf-8") as f:
    FACTS = json.load(f)


def resolve_signing_key() -> str:
    """Platform-managed signing key. Never asked from the caller.

    Precedence, resolved once at process start:
      1. `GGEN_SIGNING_KEY` already in the environment (operator-injected, e.g. from a
         k8s Secret) -- used as-is, never overwritten.
      2. A previously-generated key at SIGNING_KEY_PATH.
      3. Freshly generated 32-byte hex seed, persisted to SIGNING_KEY_PATH with 0600 perms.
    """
    env_key = os.environ.get("GGEN_SIGNING_KEY")
    if env_key:
        return env_key
    if SIGNING_KEY_PATH.exists():
        return SIGNING_KEY_PATH.read_text(encoding="utf-8").strip()
    SIGNING_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_hex(32)
    SIGNING_KEY_PATH.write_text(key, encoding="utf-8")
    os.chmod(SIGNING_KEY_PATH, 0o600)
    return key


SIGNING_KEY = resolve_signing_key()


def run_ggen(args: list[str], cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["GGEN_SIGNING_KEY"] = SIGNING_KEY
    return subprocess.run(
        [GGEN_BIN, *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# The scaffold `ggen init` produces has default rules that fail strict-mode validation
# ([FM-CONFIG-003] E0011/E0013: CONSTRUCT/SELECT queries must have ORDER BY for
# deterministic output) -- confirmed by running the real scaffold unmodified. This patch
# is the minimal real fix, not a workaround of anything ggen-specific to this service.
_MANIFEST_PATCHES = [
    (
        'construct = "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"',
        'construct = "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o } ORDER BY ?s ?p ?o"',
    ),
    ("LIMIT 10\n\"\"\" }", "ORDER BY ?class\nLIMIT 10\n\"\"\" }"),
]


def patch_manifest_for_strict_mode(manifest_path: Path) -> bool:
    text = manifest_path.read_text(encoding="utf-8")
    applied = False
    for needle, replacement in _MANIFEST_PATCHES:
        if needle in text:
            text = text.replace(needle, replacement)
            applied = True
    manifest_path.write_text(text, encoding="utf-8")
    return applied


def provision(ontology: str, packs: list[str]) -> tuple[int, dict]:
    if not GGEN_BIN or not shutil.which(GGEN_BIN):
        return 503, {
            "error": "ggen binary not found",
            "detail": f"GGEN_BIN={GGEN_BIN!r} is not an executable on PATH in this "
            "container. The real sync pipeline cannot be invoked. This service "
            "was not deployed with the ggen binary baked in -- see prep.sh/Dockerfile.",
        }

    run_id = uuid.uuid4().hex
    run_dir = WORKSPACE_ROOT / f"run-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=False)

    init = run_ggen(["init", "--path", ".", "--force", "true", "--format", "json"], run_dir)
    if init.returncode != 0:
        return 502, {
            "error": "ggen init failed",
            "stage": "init",
            "returncode": init.returncode,
            "stdout": init.stdout,
            "stderr": init.stderr,
        }

    domain_ttl = run_dir / "schema" / "domain.ttl"
    domain_ttl.parent.mkdir(parents=True, exist_ok=True)
    domain_ttl.write_text(ontology, encoding="utf-8")

    manifest_path = run_dir / "ggen.toml"
    manifest_patched = manifest_path.exists() and patch_manifest_for_strict_mode(manifest_path)

    packs_result = []
    for pack_id in packs:
        p = run_ggen(["packs", "install", "--pack-id", pack_id, "--format", "json"], run_dir)
        entry = {"pack_id": pack_id, "returncode": p.returncode}
        if p.returncode == 0:
            try:
                entry["result"] = json.loads(p.stdout)
            except json.JSONDecodeError:
                entry["result"] = p.stdout
        else:
            entry["error"] = p.stderr
        packs_result.append(entry)

    sync = run_ggen(["sync", "run", "--format", "json"], run_dir, timeout=SYNC_TIMEOUT_S)
    if sync.returncode != 0:
        return 502, {
            "error": "ggen sync run failed",
            "stage": "sync",
            "run_id": run_id,
            "manifest_patched_for_strict_mode": manifest_patched,
            "packs": packs_result,
            "returncode": sync.returncode,
            "stdout": sync.stdout,
            "stderr": sync.stderr,
        }

    try:
        sync_report = json.loads(sync.stdout)
    except json.JSONDecodeError:
        return 502, {
            "error": "ggen sync run produced non-JSON stdout",
            "run_id": run_id,
            "stdout": sync.stdout,
            "stderr": sync.stderr,
        }

    receipt_path = run_dir / ".ggen-v2" / "receipt.json"
    receipt = None
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    verify = run_ggen(["receipt", "verify", "--format", "json"], run_dir)
    try:
        verification = json.loads(verify.stdout) if verify.returncode == 0 else None
    except json.JSONDecodeError:
        verification = None

    artifacts = {}
    for rel_path in sync_report.get("written", []):
        artifact_path = run_dir / rel_path
        if artifact_path.exists():
            try:
                artifacts[rel_path] = artifact_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                artifacts[rel_path] = None

    return 200, {
        "run_id": run_id,
        "manifest_patched_for_strict_mode": manifest_patched,
        "packs": packs_result,
        "sync": sync_report,
        "artifacts": artifacts,
        "receipt": receipt,
        "receipt_verification": {
            "returncode": verify.returncode,
            "result": verification,
            "stderr": None if verify.returncode == 0 else verify.stderr,
        },
    }


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._json(200, {"status": "ok"})
        elif self.path == "/status":
            self._json(200, FACTS)
        else:
            self._json(404, {"error": "not found", "path": self.path})

    def do_POST(self) -> None:
        if self.path != "/provision":
            self._json(404, {"error": "not found", "path": self.path})
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw or b"{}")
        except json.JSONDecodeError as e:
            self._json(400, {"error": "invalid JSON body", "detail": str(e)})
            return

        ontology = body.get("ontology")
        if not isinstance(ontology, str) or not ontology.strip():
            self._json(400, {"error": "'ontology' (TTL string) is required"})
            return
        packs = body.get("packs", [])
        if not isinstance(packs, list) or not all(isinstance(p, str) for p in packs):
            self._json(400, {"error": "'packs' must be a list of strings"})
            return

        try:
            code, payload = provision(ontology, packs)
        except subprocess.TimeoutExpired as e:
            self._json(504, {"error": "ggen subprocess timed out", "detail": str(e)})
            return
        self._json(code, payload)

    def log_message(self, fmt: str, *args) -> None:  # quieter, structured-ish stdout
        print(f"{self.address_string()} - {fmt % args}")


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"listening on :{port} (facts from {FACTS_PATH}, ggen bin {GGEN_BIN})")
    server.serve_forever()


if __name__ == "__main__":
    main()
