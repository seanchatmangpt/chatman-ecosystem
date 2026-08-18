"""Minimal stdlib HTTP status service.

Serves two endpoints, no auth, no external dependencies:
  GET /healthz -> 200 {"status": "ok"}                (k8s liveness probe)
  GET /status  -> 200 <contents of facts.json>         (real, build-time-baked facts)

facts.json is produced by this service's prep.sh at image-build time by reading
the real project directory on disk (COPYed into the image, not read at runtime --
the running container has no access to the host repos). No field in facts.json is
computed or guessed by this app; it only reads and re-serves what prep.sh captured.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FACTS_PATH = os.environ.get("FACTS_PATH", "/app/facts.json")

with open(FACTS_PATH, "r", encoding="utf-8") as f:
    FACTS = json.load(f)


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

    def log_message(self, fmt: str, *args) -> None:  # quieter, structured-ish stdout
        print(f"{self.address_string()} - {fmt % args}")


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"listening on :{port} (facts from {FACTS_PATH})")
    server.serve_forever()


if __name__ == "__main__":
    main()
