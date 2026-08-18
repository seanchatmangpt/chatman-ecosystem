"""ggen-marketplace service: health/status stub + a real registry query frontend.

Endpoints:
  GET  /healthz -> 200 {"status": "ok"}                (k8s liveness probe, unchanged)
  GET  /status  -> 200 <contents of facts.json>         (unchanged, build-time-baked facts)
  GET  /packs   -> runs the REAL `ggen pack list` CLI command via subprocess and returns
                   its real JSON output -- the packs actually registered in the ggen pack
                   registry this binary resolves (GGEN_PACKS_DIR, see below), not a
                   hardcoded or synthesized list.
  POST /query   -> runs the REAL `ggen pack query <sparql> [--pack-id <id>]` CLI command
                   (a raw SPARQL query over pack RDF facts) via subprocess and returns its
                   real JSON output.

Why subprocess, not an in-process Python binding
--------------------------------------------------
Same rationale as services/ggen/app.py (mirrored exactly): there is no Python binding for
`ggen-marketplace`/`ggen-cli` -- no PyO3/maturin wheel, no FFI shim in this repo. Shelling
out to the real, already-compiled `ggen` binary and parsing its real JSON stdout is the
established pattern (castle -> autofde-lab/gymact subprocess+JSON bridge; services/ggen/
app.py's own `provision`/`run_ggen`). Nothing here is simulated -- if the binary is missing
or a query/list fails, the failure is reported verbatim (stdout/stderr/returncode), never
swallowed into a synthesized "ok" or a fabricated result set.

The real CLI surface (confirmed this session, not assumed)
-------------------------------------------------------------
`ggen pack --help` against the locally-built debug binary
(`/Users/sac/ggen/target/debug/ggen`, version 26.8.12) is the version that actually has a
`query` subcommand -- the separately cargo-installed `/Users/sac/.local/bin/ggen` (26.8.8)
does NOT (`ggen pack query --help` there fails with "unrecognized subcommand 'query'").
`GGEN_BIN` must therefore point at a binary built from a workspace revision that includes
`ggen pack query` (`crates/ggen-cli/src/cmds/pack.rs`'s `query` verb, backed by
`ggen_marketplace::packs_registry::sparql_executor::run_pack_query` -- the same function
`ggen-mcp`'s `pack_query` tool wraps, per that tool's own doc comment: "Thin adapter around
... the single implementation shared with the `ggen pack query` CLI verb").

Confirmed contract:
  `ggen pack list --format json`
      -> {"packs": [...], "total": N}
  `ggen pack query <SPARQL> [--pack-id <ID>] --format json`
      -> {"scope": "all-packs"|"pack:<id>", "packs_queried": N,
          "columns": [...], "rows": [[...], ...], "row_count": N,
          "execution_time_ms": N}
      -- omitting --pack-id unions every pack the registry resolves into one SPARQL query
         (`scope: "all-packs"`); passing --pack-id scopes to that one pack's RDF facts
         (`scope: "pack:<id>"`). A pack-id that does not resolve, or invalid SPARQL, exits
         non-zero with a real CLI error on stderr -- both are surfaced verbatim below as a
         502, never coerced into an empty success.

Real, confirmed limitation of pack registry scope
----------------------------------------------------
`ggen pack list`/`ggen pack query` resolve their pack set via
`ggen_marketplace::packs_registry::metadata::try_get_packs_dir()`, whose real resolution
order is: `GGEN_PACKS_DIR` env var, then `./marketplace/packs` (and `../`, `../../`
relative variants), then `~/.ggen/packs`. That directory format is one `<pack-id>.toml`
file per pack (a `PackFile`/`Pack` TOML manifest) -- it is NOT the ~/ggen-marketplace/packs/
source-tree layout (147+ subdirectories, each with its own `ontology.ttl`, `Cargo.toml`,
etc.), which has zero top-level `.toml` files and is not consumable by this resolver as-is.
Confirmed live on this host: `~/.ggen/packs/` (the resolver's real home-directory fallback,
and this service's `GGEN_PACKS_DIR` default) contains exactly two real registered packs
(`framework-lsp.toml`, `tower-lsp-max.toml`) -- so `GET /packs` and `POST /query` here are
real and unfabricated, but scoped to those two packs, not the full 147-pack marketplace
source tree. Making the full marketplace tree queryable would require either converting
each pack dir into this resolver's `.toml` format or extending `try_get_packs_dir`'s
resolution to understand that tree's layout -- both out of scope for this pass, which
mirrors the CLI's real, already-shipped contract rather than building a new one.
"""
import json
import os
import shutil
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FACTS_PATH = os.environ.get("FACTS_PATH", "/app/facts.json")
GGEN_BIN = os.environ.get("GGEN_BIN", "/usr/local/bin/ggen")
GGEN_PACKS_DIR = os.environ.get("GGEN_PACKS_DIR", "")
QUERY_TIMEOUT_S = int(os.environ.get("GGEN_QUERY_TIMEOUT_S", "30"))

with open(FACTS_PATH, "r", encoding="utf-8") as f:
    FACTS = json.load(f)


def run_ggen(args: list[str], timeout: int = 15) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if GGEN_PACKS_DIR:
        env["GGEN_PACKS_DIR"] = GGEN_PACKS_DIR
    return subprocess.run(
        [GGEN_BIN, *args],
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def binary_available() -> bool:
    return bool(GGEN_BIN) and bool(shutil.which(GGEN_BIN))


def list_packs() -> tuple[int, dict]:
    if not binary_available():
        return 503, {
            "error": "ggen binary not found",
            "detail": f"GGEN_BIN={GGEN_BIN!r} is not an executable on PATH in this "
            "container. The real pack registry cannot be listed. This service was "
            "not deployed with a ggen build that has `pack list`/`pack query` -- "
            "see prep.sh/Dockerfile.",
        }
    try:
        result = run_ggen(["pack", "list", "--format", "json"])
    except subprocess.TimeoutExpired as e:
        return 504, {"error": "ggen pack list timed out", "detail": str(e)}

    if result.returncode != 0:
        return 502, {
            "error": "ggen pack list failed",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return 502, {
            "error": "ggen pack list produced non-JSON stdout",
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    return 200, payload


def run_pack_query(sparql: str, pack_id: str | None) -> tuple[int, dict]:
    if not binary_available():
        return 503, {
            "error": "ggen binary not found",
            "detail": f"GGEN_BIN={GGEN_BIN!r} is not an executable on PATH in this "
            "container. The real SPARQL query cannot be run. This service was not "
            "deployed with a ggen build that has `pack query` -- see prep.sh/Dockerfile.",
        }
    args = ["pack", "query", sparql, "--format", "json"]
    if pack_id:
        args.extend(["--pack-id", pack_id])
    try:
        result = run_ggen(args, timeout=QUERY_TIMEOUT_S)
    except subprocess.TimeoutExpired as e:
        return 504, {"error": "ggen pack query timed out", "detail": str(e)}

    if result.returncode != 0:
        return 502, {
            "error": "ggen pack query failed",
            "sparql": sparql,
            "pack_id": pack_id,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return 502, {
            "error": "ggen pack query produced non-JSON stdout",
            "sparql": sparql,
            "pack_id": pack_id,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    return 200, payload


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
        elif self.path == "/packs":
            code, payload = list_packs()
            self._json(code, payload)
        else:
            self._json(404, {"error": "not found", "path": self.path})

    def do_POST(self) -> None:
        if self.path != "/query":
            self._json(404, {"error": "not found", "path": self.path})
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw or b"{}")
        except json.JSONDecodeError as e:
            self._json(400, {"error": "invalid JSON body", "detail": str(e)})
            return

        sparql = body.get("sparql")
        if not isinstance(sparql, str) or not sparql.strip():
            self._json(400, {"error": "'sparql' (query string) is required"})
            return
        pack_id = body.get("pack_id")
        if pack_id is not None and (not isinstance(pack_id, str) or not pack_id.strip()):
            self._json(400, {"error": "'pack_id', if provided, must be a non-empty string"})
            return

        code, payload = run_pack_query(sparql, pack_id)
        self._json(code, payload)

    def log_message(self, format: str, *args) -> None:  # quieter, structured-ish stdout
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"listening on :{port} (facts from {FACTS_PATH}, ggen bin {GGEN_BIN}, "
          f"packs dir {GGEN_PACKS_DIR or '(resolver default)'})")
    server.serve_forever()


if __name__ == "__main__":
    main()
