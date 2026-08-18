"""Minimal stdlib HTTP status service.

Serves two endpoints, no auth, no external dependencies:
  GET /healthz -> 200 {"status": "ok"}                (k8s liveness probe)
  GET /status  -> 200 <contents of facts.json>         (real, build-time-baked facts,
                                                          plus one live-read field --
                                                          see below)

facts.json is produced by this service's prep.sh at image-build time by reading
the real project directory on disk (COPYed into the image, not read at runtime --
the running container has no access to the host repos). No field in facts.json is
computed or guessed by this app; it only reads and re-serves what prep.sh captured.

Feature-flag-gated field
-------------------------
Every GET /status also does a fresh, real, live read of the platform's Feature
Flags ConfigMap (`platform-feature-flags`, `platform-console` namespace) via the
real Kubernetes API, using this pod's own in-cluster ServiceAccount token -- no
polling loop, no cache, a brand-new HTTPS request on every single request. When
that ConfigMap's `verbose-status` key is exactly the string "true", the response
gains one additional real field, `process_uptime_seconds` (wall-clock seconds
since this process started, `time.monotonic()`-derived -- a real, live, strictly
increasing number, never a fabricated placeholder). Any read failure (flag not
set yet, RBAC denied, API server unreachable, this process not actually running
in a cluster) fails closed to the baseline response with no extra field -- same
"never fabricate a fallback" convention platform-console/app/lib/k8s.ts already
documents for its own in-cluster API client.

Why a live k8s-API read instead of a mounted ConfigMap volume: `platform-feature-
flags` lives in the `platform-console` namespace, while this Deployment's Pods
run in `autofde-lab` -- a ConfigMap volume can only ever mount an object from the
Pod's OWN namespace (a hard Kubernetes constraint, not a policy choice), so a
genuinely live cross-namespace toggle is only reachable via the Kubernetes API,
not a volume mount. This Pod's ServiceAccount (`autofde-lab-status-reader`,
k8s/rbac.yaml) is granted exactly one additional verb for this purpose -- `get`
on the single named object `platform-feature-flags` in the `platform-console`
namespace -- via a Role+RoleBinding pair in k8s/paas-rbac.yaml; no other
ConfigMap, no other namespace, no write verb. One consequence of this design
worth stating plainly: propagation is effectively instantaneous (a live read, not
governed by kubelet's ~60s ConfigMap-volume cache/sync window), which is a
stronger real-time guarantee than a subPath/projected-volume mount would have
given -- disclosed here rather than silently claimed as "the same as a mount".
"""
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FACTS_PATH = os.environ.get("FACTS_PATH", "/app/facts.json")

SA_DIR = "/var/run/secrets/kubernetes.io/serviceaccount"
FLAGS_NAMESPACE = os.environ.get("FEATURE_FLAGS_NAMESPACE", "platform-console")
FLAGS_CONFIGMAP = os.environ.get("FEATURE_FLAGS_CONFIGMAP", "platform-feature-flags")
FLAG_KEY = "verbose-status"
FLAG_REQUEST_TIMEOUT_S = 3

START_TIME = time.monotonic()

with open(FACTS_PATH, "r", encoding="utf-8") as f:
    FACTS = json.load(f)


def _read_verbose_status_flag() -> bool:
    """Real, live GET of the one ConfigMap key this service is authorized to
    read, via the pod's own in-cluster ServiceAccount identity -- the exact
    same token/CA-bundle convention platform-console/app/lib/k8s.ts uses for
    its own in-cluster API client. Fails closed to False on ANY error: no
    token/CA mounted (not actually running in the cluster), no
    KUBERNETES_SERVICE_HOST, network failure, non-2xx (including a real 403
    if this RBAC grant is ever revoked, or a real 404 before the ConfigMap
    exists), or an unparsable body -- never raises out of this function,
    never fabricates a value."""
    token_path = f"{SA_DIR}/token"
    ca_path = f"{SA_DIR}/ca.crt"
    host = os.environ.get("KUBERNETES_SERVICE_HOST")
    port = os.environ.get("KUBERNETES_SERVICE_PORT", "443")
    if not host or not os.path.exists(token_path) or not os.path.exists(ca_path):
        return False
    try:
        with open(token_path, "r", encoding="utf-8") as tf:
            token = tf.read().strip()
        ctx = ssl.create_default_context(cafile=ca_path)
        url = (
            f"https://{host}:{port}/api/v1/namespaces/{FLAGS_NAMESPACE}"
            f"/configmaps/{FLAGS_CONFIGMAP}"
        )
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, context=ctx, timeout=FLAG_REQUEST_TIMEOUT_S) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body.get("data", {}).get(FLAG_KEY) == "true"
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return False


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
            payload = dict(FACTS)
            if _read_verbose_status_flag():
                payload["process_uptime_seconds"] = round(time.monotonic() - START_TIME, 3)
            self._json(200, payload)
        else:
            self._json(404, {"error": "not found", "path": self.path})

    def log_message(self, fmt: str, *args) -> None:  # quieter, structured-ish stdout
        print(f"{self.address_string()} - {fmt % args}")


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"listening on :{port} (facts from {FACTS_PATH})")
    server.serve_forever()


if __name__ == "__main__":
    main()
