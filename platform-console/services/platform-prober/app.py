"""Minimal stdlib Prometheus exporter that performs REAL reachability checks
against every platform component on every scrape, no external dependencies.

Why this exists: Prometheus's own `up` metric is generated per scrape target
(one series per ServiceMonitor endpoint it scrapes), which requires the
target itself to serve a Prometheus-text-format /metrics endpoint. Two of
this platform's 8 status-page components are third-party images we do not
control (supabase/gotrue, postgrest/postgrest) and one (Postgres) is not
HTTP at all -- none of the three expose /metrics. Rather than fabricate a
number for those three, this exporter does the same thing a real
hyperscaler status page's synthetic-canary layer does: it makes a genuine
network call to each component on every single scrape (no caching, no
memoized last-known-state) and reports the real outcome as a Prometheus
gauge literally named `up`, distinguished by a `component` label:

    up{component="gymact-status"} 1
    up{component="demo-project-postgres"} 0

Prometheus scrapes this exporter itself (see k8s ServiceMonitor
`platform-prober`), so every sample of every `up{component=...}` series
already carries a real Prometheus timestamp -- lib/status-page.ts's
avg_over_time(up{component="..."}[<window>]) queries are averaging real,
timestamped, previously-recorded samples, not numbers computed at request
time.

Deliberately co-located in the platform-console namespace: that namespace
carries no NetworkPolicy (see k8s/network-policies.yaml's own header
comment), and the 4 project namespaces already carry an
`*-allow-from-platform-console` Ingress rule on port 8080 for exactly this
kind of platform-console-namespace caller -- so this exporter reaches every
target it needs to without any NetworkPolicy changes, and Prometheus
(monitoring namespace, also unrestricted) can freely scrape it back.
"""
import json
import os
import socket
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HTTP_TIMEOUT_S = float(os.environ.get("PROBE_TIMEOUT_S", "2.5"))
TCP_TIMEOUT_S = float(os.environ.get("PROBE_TCP_TIMEOUT_S", "2.0"))

# Real, live in-cluster Service DNS names + ports/paths for every status-page
# component. Overridable via env for local testing; the k8s Deployment sets
# the real cluster-internal defaults explicitly (see
# k8s/services-and-deployments.yaml) so this table is redundant with those
# env vars in production, same convention as lib/status.ts's *_STATUS_URL.
HTTP_TARGETS = [
    {
        "component": "autofde-lab-status",
        "url": os.environ.get(
            "PROBE_AUTOFDE_LAB_URL",
            "http://autofde-lab-status.autofde-lab.svc.cluster.local/healthz",
        ),
    },
    {
        "component": "gymact-status",
        "url": os.environ.get(
            "PROBE_GYMACT_URL", "http://gymact-status.gymact.svc.cluster.local/healthz"
        ),
    },
    {
        "component": "ggen-status",
        "url": os.environ.get(
            "PROBE_GGEN_URL", "http://ggen-status.ggen.svc.cluster.local/healthz"
        ),
    },
    {
        "component": "ggen-marketplace-status",
        "url": os.environ.get(
            "PROBE_GGEN_MARKETPLACE_URL",
            "http://ggen-marketplace-status.ggen-marketplace.svc.cluster.local/healthz",
        ),
    },
    {
        "component": "platform-console-gateway",
        "url": os.environ.get(
            "PROBE_PLATFORM_CONSOLE_URL",
            "http://platform-console-gateway.platform-console.svc.cluster.local:8080/login",
        ),
    },
    {
        "component": "demo-project-auth",
        "url": os.environ.get(
            "PROBE_DEMO_AUTH_URL",
            "http://demo-project-auth.supabase-demo.svc.cluster.local:9999/health",
        ),
    },
    {
        "component": "demo-project-rest",
        "url": os.environ.get(
            "PROBE_DEMO_REST_URL",
            "http://demo-project-rest.supabase-demo.svc.cluster.local:3000/",
        ),
    },
]

# Postgres is not HTTP -- a real TCP connect is the genuine reachability
# check (the same technique blackbox_exporter's `tcp_connect` module uses).
TCP_TARGETS = [
    {
        "component": "demo-project-postgres",
        "host": os.environ.get(
            "PROBE_DEMO_POSTGRES_HOST", "demo-db-postgres.supabase-demo.svc.cluster.local"
        ),
        "port": int(os.environ.get("PROBE_DEMO_POSTGRES_PORT", "5432")),
    },
]


def probe_http(url: str) -> tuple[bool, float, str]:
    started = time.monotonic()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "platform-prober/1.0"})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            ok = 200 <= resp.status < 500  # a real HTTP response, even 4xx, means reachable/alive
            duration = time.monotonic() - started
            return ok, duration, f"http {resp.status}"
    except urllib.error.HTTPError as e:
        duration = time.monotonic() - started
        # Server answered (it is reachable) but with an error status.
        return (200 <= e.code < 500), duration, f"http {e.code}"
    except Exception as e:  # DNS failure, connection refused, timeout, etc.
        duration = time.monotonic() - started
        return False, duration, f"error: {e}"


def probe_tcp(host: str, port: int) -> tuple[bool, float, str]:
    started = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=TCP_TIMEOUT_S):
            duration = time.monotonic() - started
            return True, duration, "tcp connect ok"
    except Exception as e:
        duration = time.monotonic() - started
        return False, duration, f"error: {e}"


def collect() -> list[dict]:
    """Runs every real check now and returns the real results. Called fresh
    on every /metrics scrape -- nothing here is cached between requests."""
    results = []
    for target in HTTP_TARGETS:
        ok, duration, detail = probe_http(target["url"])
        results.append(
            {
                "component": target["component"],
                "up": ok,
                "duration_s": duration,
                "detail": detail,
                "checked_at": time.time(),
            }
        )
    for target in TCP_TARGETS:
        ok, duration, detail = probe_tcp(target["host"], target["port"])
        results.append(
            {
                "component": target["component"],
                "up": ok,
                "duration_s": duration,
                "detail": detail,
                "checked_at": time.time(),
            }
        )
    return results


def render_prometheus_text(results: list[dict]) -> str:
    lines = [
        "# HELP up Real reachability check (1 = last probe succeeded, 0 = it did not), per platform component.",
        "# TYPE up gauge",
    ]
    for r in results:
        lines.append(f'up{{component="{r["component"]}"}} {1 if r["up"] else 0}')
    lines.append("")
    lines.append(
        "# HELP platform_prober_probe_duration_seconds Real wall-clock duration of the last probe, per component."
    )
    lines.append("# TYPE platform_prober_probe_duration_seconds gauge")
    for r in results:
        lines.append(
            f'platform_prober_probe_duration_seconds{{component="{r["component"]}"}} {r["duration_s"]:.6f}'
        )
    return "\n".join(lines) + "\n"


class Handler(BaseHTTPRequestHandler):
    def _text(self, code: int, body: str, content_type: str = "text/plain; version=0.0.4") -> None:
        payload = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._text(200, json.dumps({"status": "ok"}), "application/json")
        elif self.path == "/metrics":
            results = collect()
            self._text(200, render_prometheus_text(results))
        elif self.path == "/debug":
            # Human-readable version of the same real results, for manual
            # verification without needing to parse Prometheus text format.
            results = collect()
            self._text(200, json.dumps(results, indent=2), "application/json")
        else:
            self._text(404, json.dumps({"error": "not found", "path": self.path}), "application/json")

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"platform-prober listening on :{port} -- {len(HTTP_TARGETS)} HTTP + {len(TCP_TARGETS)} TCP targets")
    server.serve_forever()


if __name__ == "__main__":
    main()
