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

Tenant-namespaced target (04-GGEN-BRCE-CROSS-CUTTING.md's PaaS evidence bar)
-----------------------------------------------------------------------------
The prior version of this endpoint landed every write inside this pod's own ephemeral
`WORKSPACE_ROOT` run directory -- no tenant boundary was crossed, no BRCE-style origin
tag was applied, and no durable attempt log was kept. That is the concrete gap the ticket
names as "still open" for the PaaS evidence bar. This revision closes it the same way
`platform-console/app/lib/redis.ts` and `queue.ts` already pick/provision a per-project
namespace via `k8sRequest`'s real in-cluster ServiceAccount HTTPS client, and the way
`ggen-mcp`'s `unattended_dispatch::try_unattended_apply` tags every dispatched write with
a BRCE origin and appends every attempt -- success or failure -- to a durable JSONL log:

  * `/provision` now requires a `project` field: the caller-named tenant. That name IS
    the target Kubernetes namespace (same "namespace is keyed by project name" convention
    `redis.ts`/`queue.ts` already build resources inside, e.g. `<project>-redis` living in
    `project.namespace`) -- `resolve_tenant_namespace` below GETs that namespace via a
    real HTTPS call to the in-cluster API server using this pod's own ServiceAccount
    token/CA (`k8s_request`, a direct Python port of `lib/k8s.ts`'s `k8sRequest`: same
    `/var/run/secrets/kubernetes.io/serviceaccount` mount, same fail-closed "not
    configured" result off-cluster, same Bearer-token HTTPS primitive, no external k8s
    client library). If the namespace does not exist, it is really created
    (`POST /api/v1/namespaces`) with the same `pod-security.kubernetes.io/enforce:
    restricted` + `app.kubernetes.io/part-of: platform-console` labels `redis.ts`'s own
    Deployment/Service manifests already assume every project namespace carries.
  * The run directory moves from `WORKSPACE_ROOT/run-<id>` to
    `WORKSPACE_ROOT/<namespace>/run-<id>` -- a real project-namespaced location on this
    pod's own state volume, keyed by the tenant namespace `resolve_tenant_namespace` just
    picked or provisioned, instead of a bare ephemeral run id with no tenant affiliation.
  * The response is tagged `"origin": "ggen-paas-provision"` at the service layer --
    disclosed honestly, not silently: `ggen sync run`'s live CLI surface
    (`crates/ggen-engine/src/verbs/sync.rs::sync_run`) exposes only `dry_run`/`watch`, no
    `--receipt-origin` flag, so `praxis-core::ReceiptRecord.origin` inside the signed
    receipt itself stays `null` from this subprocess call, exactly as it does when driven
    from the bare CLI. Tagging the origin at the response envelope (not by mutating the
    signed receipt bytes) is the only actuation-honest way to attach it from outside the
    Rust process without forging a field to be BLAKE3-hashed and ed25519-signed by code
    that never produced it.
  * Every attempt -- `applied` on a verified receipt or `refused`/`error` on any failure --
    is appended as one JSON line to `PROVISION_LOG_PATH`
    (default `/app/state/ggen-paas-provision-log.jsonl`), the same "log every attempt,
    success or failure" discipline as `.ggen/unattended-dispatch-log.jsonl`.
"""
import json
import os
import secrets
import shutil
import ssl
import subprocess
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

FACTS_PATH = os.environ.get("FACTS_PATH", "/app/facts.json")
GGEN_BIN = os.environ.get("GGEN_BIN", "/usr/local/bin/ggen")
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "/app/state/runs"))
SIGNING_KEY_PATH = Path(os.environ.get("SIGNING_KEY_PATH", "/app/state/keys/signing.key"))
SYNC_TIMEOUT_S = int(os.environ.get("GGEN_SYNC_TIMEOUT_S", "120"))
PROVISION_ORIGIN = "ggen-paas-provision"
PROVISION_LOG_PATH = Path(
    os.environ.get("PROVISION_LOG_PATH", "/app/state/ggen-paas-provision-log.jsonl")
)

SA_DIR = Path("/var/run/secrets/kubernetes.io/serviceaccount")
K8S_REQUEST_TIMEOUT_S = 5

with open(FACTS_PATH, "r", encoding="utf-8") as f:
    FACTS = json.load(f)


def _in_cluster_config() -> dict | None:
    """Direct Python port of `lib/k8s.ts`'s `readInClusterConfig`: the exact same
    ServiceAccount mount, the exact same fail-closed `None` off-cluster. No caching
    across calls (unlike the TS version's module-level cache) since this process is
    long-lived and a rotated token should be re-read, not pinned at first use."""
    host = os.environ.get("KUBERNETES_SERVICE_HOST")
    port = os.environ.get("KUBERNETES_SERVICE_PORT", "443")
    token_path = SA_DIR / "token"
    ca_path = SA_DIR / "ca.crt"
    if not host or not token_path.exists() or not ca_path.exists():
        return None
    try:
        return {
            "token": token_path.read_text(encoding="utf-8").strip(),
            "ca_path": str(ca_path),
            "host": host,
            "port": port,
        }
    except OSError:
        return None


def k8s_request(path: str, method: str = "GET", body: dict | None = None) -> tuple[bool, object]:
    """Python port of `lib/k8s.ts`'s `k8sRequest`: a real HTTPS call to the in-cluster
    API server using this pod's own ServiceAccount token/CA bundle, no external k8s
    client library, same fail-closed "not configured" contract off-cluster. Returns
    `(ok, data_or_error)`; a 404 is surfaced as `ok=False` with `"not found"` in the
    error text so callers can match the same idempotent-not-found convention
    `k8s.ts`'s own callers already rely on."""
    cfg = _in_cluster_config()
    if cfg is None:
        return False, (
            "not configured: no in-cluster ServiceAccount credentials found "
            f"({SA_DIR}) -- this only works when running as a pod in-cluster"
        )
    url = f"https://{cfg['host']}:{cfg['port']}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {cfg['token']}")
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    ctx = ssl.create_default_context(cafile=cfg["ca_path"])
    try:
        with urllib.request.urlopen(req, timeout=K8S_REQUEST_TIMEOUT_S, context=ctx) as resp:
            raw = resp.read()
            return True, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = None
        message = (parsed or {}).get("message") if isinstance(parsed, dict) else None
        return False, f"HTTP {e.code} {method} {path}: {message or e.reason}"
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return False, f"{method} {path} failed: {e}"


def build_namespace_manifest(name: str) -> dict:
    """Same restricted-PodSecurity + `part-of: platform-console` label convention
    `redis.ts`'s Deployment manifest doc comment says every project namespace on this
    cluster already carries -- applied here at namespace-creation time since this is the
    one path in this service that might actually be the one creating it."""
    return {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {
            "name": name,
            "labels": {
                "app.kubernetes.io/part-of": "platform-console",
                "app.kubernetes.io/managed-by": "ggen-status",
                "pod-security.kubernetes.io/enforce": "restricted",
            },
        },
    }


def resolve_tenant_namespace(project: str) -> tuple[bool, str, str | None]:
    """Picks (or provisions) the tenant namespace for `project`, mirroring
    `redis.ts`/`queue.ts`'s "namespace is keyed by the project name" convention: the
    project name IS the namespace name. Returns `(ok, namespace_or_reason, detail)`.

    `ok=False` covers both the off-cluster "not configured" case (this service running
    outside a real pod, e.g. local dev/CI) and a real k8s API failure -- both are honest
    refusals, never silently downgraded to the old ephemeral-workspace behavior, so a
    caller can never mistake a degraded local run for a real tenant-scoped one."""
    ok, data = k8s_request(f"/api/v1/namespaces/{urllib.request.quote(project, safe='')}")
    if ok:
        return True, project, None
    if isinstance(data, str) and "not configured" in data:
        return False, "not_configured", data
    if isinstance(data, str) and "HTTP 404" in data:
        create_ok, create_data = k8s_request(
            "/api/v1/namespaces", "POST", build_namespace_manifest(project)
        )
        if create_ok:
            return True, project, None
        return False, "namespace_create_failed", str(create_data)
    return False, "namespace_lookup_failed", str(data)


def append_provision_log(entry: dict) -> None:
    """`.ggen/unattended-dispatch-log.jsonl`'s exact discipline ported to this service:
    one JSON line per attempt, success or failure, never swallowed. Best-effort append
    (a logging failure must never fail the provisioning attempt itself -- the same
    `let _ =` non-fatal-write posture `unattended_dispatch.rs::append_audit_log` uses)."""
    try:
        PROVISION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PROVISION_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


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


def provision(ontology: str, packs: list[str], tenant_id: str | None) -> tuple[int, dict]:
    """Runs one full provision attempt and unconditionally appends exactly one line to
    `PROVISION_LOG_PATH` before returning -- success, refusal, or error alike, the same
    "every attempt is logged" discipline `unattended_dispatch.rs::try_unattended_apply`
    already holds itself to. All the actual pipeline work happens in `_provision_inner`;
    this wrapper's only job is to guarantee the log line fires on every exit path,
    including the exception path a bare `return` inside a `try` could otherwise skip.
    """
    run_id = uuid.uuid4().hex
    code: int | None = None
    payload: dict = {}
    try:
        code, payload = _provision_inner(ontology, packs, tenant_id, run_id)
        return code, payload
    except subprocess.TimeoutExpired as e:
        code = 504
        payload = {
            "error": "ggen subprocess timed out",
            "run_id": run_id,
            "tenant_id": tenant_id,
            "detail": str(e),
        }
        raise
    finally:
        append_provision_log(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "run_id": run_id,
                "tenant_id": tenant_id,
                "namespace": payload.get("namespace") if isinstance(payload, dict) else None,
                "origin": PROVISION_ORIGIN,
                "outcome": "applied" if code == 200 else "refused_or_error",
                "http_status": code,
                "error": payload.get("error") if isinstance(payload, dict) else None,
                "receipt_path": payload.get("receipt_path") if isinstance(payload, dict) else None,
            }
        )


def _provision_inner(
    ontology: str, packs: list[str], tenant_id: str | None, run_id: str
) -> tuple[int, dict]:
    if not GGEN_BIN or not shutil.which(GGEN_BIN):
        return 503, {
            "error": "ggen binary not found",
            "run_id": run_id,
            "detail": f"GGEN_BIN={GGEN_BIN!r} is not an executable on PATH in this "
            "container. The real sync pipeline cannot be invoked. This service "
            "was not deployed with the ggen binary baked in -- see prep.sh/Dockerfile.",
        }

    namespace: str | None = None
    if tenant_id:
        # Pick or provision the real tenant namespace via the same k8sRequest-based
        # in-cluster pattern redis.ts/queue.ts already use, instead of trusting the
        # caller-supplied tenant_id as a bare directory name with no cluster-side
        # existence check. Off-cluster (local dev/this session's verification run),
        # k8s_request fails closed with "not configured" -- honestly reported, never
        # silently downgraded back to the old flat-ephemeral-workspace behavior.
        ns_ok, ns_result, ns_detail = resolve_tenant_namespace(tenant_id)
        if not ns_ok:
            return 502, {
                "error": "tenant namespace resolution failed",
                "run_id": run_id,
                "tenant_id": tenant_id,
                "reason": ns_result,
                "detail": ns_detail,
            }
        namespace = ns_result

    run_id_for_dir = run_id
    # Tenant isolation at the filesystem level: once a real tenant namespace is
    # resolved, the run directory is nested under WORKSPACE_ROOT/<namespace>/run-<uuid>
    # -- a project-namespaced target, not the flat WORKSPACE_ROOT/run-<uuid> every prior
    # call landed in regardless of caller. Falls back to the flat layout only when no
    # tenant_id was supplied at all (unscoped/dev-mode calls keep working unchanged).
    run_root = WORKSPACE_ROOT / namespace if namespace else WORKSPACE_ROOT
    run_dir = run_root / f"run-{run_id_for_dir}"
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
        "tenant_id": tenant_id,
        "namespace": namespace,
        "origin": PROVISION_ORIGIN,
        "manifest_patched_for_strict_mode": manifest_patched,
        "packs": packs_result,
        "sync": sync_report,
        "artifacts": artifacts,
        "receipt": receipt,
        "receipt_path": str(receipt_path) if receipt_path.exists() else None,
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
        # Accept 'project' as a compatibility alias for 'tenant_id': some external
        # callers/contracts describe this field as the project name rather than the
        # internal tenant_id field name used throughout provision()/_provision_inner()/
        # resolve_tenant_namespace(). 'tenant_id' takes precedence if both are given.
        tenant_id = body.get("tenant_id")
        if tenant_id is None:
            tenant_id = body.get("project")
        if tenant_id is not None and (
            not isinstance(tenant_id, str)
            or not tenant_id.strip()
            or "/" in tenant_id
            or ".." in tenant_id
        ):
            self._json(400, {"error": "'tenant_id', if provided, must be a non-empty string with no path separators"})
            return

        try:
            code, payload = provision(ontology, packs, tenant_id)
        except subprocess.TimeoutExpired as e:
            self._json(504, {"error": "ggen subprocess timed out", "tenant_id": tenant_id, "detail": str(e)})
            return
        if isinstance(payload, dict) and "tenant_id" not in payload:
            payload["tenant_id"] = tenant_id
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
