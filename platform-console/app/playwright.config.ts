import { defineConfig, devices } from "@playwright/test";
import fs from "fs";
import path from "path";

// Load the gitignored .env.local (see its own header comment) for
// E2E_BASE_HOST / E2E_BASE_PORT / E2E_HOST_HEADER / E2E_ADMIN_USERNAME /
// E2E_ADMIN_PASSWORD. Hand-rolled (no `dotenv` dependency) -- just enough
// to read KEY=VALUE lines, skipping blanks/comments.
const envLocalPath = path.resolve(__dirname, ".env.local");
if (fs.existsSync(envLocalPath)) {
  for (const line of fs.readFileSync(envLocalPath, "utf-8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    const value = trimmed.slice(eq + 1).trim();
    if (!(key in process.env)) process.env[key] = value;
  }
}

/**
 * Real E2E config -- points at the LIVE kind-platform-eng-colima cluster's
 * real Istio ingress gateway, not a local `next dev`/`next start` server.
 * There is deliberately no `webServer` block: the app under test is the
 * already-deployed platform-console-gateway Deployment, reached through
 * the real istio-ingressgateway Service's NodePort.
 *
 * Host routing without editing /etc/hosts (a system-settings change this
 * agent does not make on the user's behalf): Istio's VirtualService
 * (k8s/gateway.yaml) routes strictly on the `platform.local` Host header
 * -- confirmed live that a bare-IP request with no Host header gets a real
 * 404 from Envoy, only `Host: platform.local` gets a real 200. Setting a
 * `Host` override via Playwright's own `extraHTTPHeaders` or a
 * `page.route` header rewrite both fail against real Chromium navigation
 * (`net::ERR_INVALID_ARGUMENT`, or a silently-dropped Host on
 * `route.continue`, respectively -- both verified against the live
 * gateway during this setup, not assumed). The approach that actually
 * works: launch Chromium with `--host-resolver-rules=MAP platform.local
 * <NodePort IP>` so the browser's own DNS resolves `platform.local` to
 * the real IP while still sending a real `Host: platform.local` header
 * (confirmed live: real 200 + real "Platform Console" page title).
 *
 * Base host/port: the ingress gateway's NodePort drifts across cluster
 * recreations (k8s/gateway.yaml's own comment is stale -- confirmed live
 * as 31594 on 2026-08-18, comment still says 31553). Re-confirm with:
 *   kubectl get svc -n istio-system istio-ingressgateway -o jsonpath='{.spec.ports}'
 * and set E2E_BASE_HOST/E2E_BASE_PORT in .env.local accordingly.
 *
 * Also: this dev cluster is `kind` running inside a `colima` VM, so the
 * NodePort is not directly reachable from the macOS host's 127.0.0.1 --
 * only the kind node's own hostPort-mapped 80/443 are (and those don't
 * carry the NodePort service). This session opened a real SSH local port
 * forward through colima to make the NodePort reachable at
 * 127.0.0.1:31594 on the host:
 *   ssh -F <(colima ssh-config) -f -N -L 31594:<kind-node-ip>:31594 colima
 * That tunnel must be running (or an equivalent `kubectl port-forward`)
 * for E2E_BASE_HOST=127.0.0.1 to work; re-open it if the shell/session
 * that started it exits.
 *
 * Auth: E2E_ADMIN_USERNAME/E2E_ADMIN_PASSWORD in .env.local are a
 * TEMPORARY local-admin password whose bcrypt hash was live-patched into
 * the platform-console-secrets Secret's ADMIN_PASSWORD_HASH for the
 * duration of E2E work (the real permanent hash is one-way and cannot be
 * used as a plaintext form value) -- restore the original hash and roll
 * the deployment again when E2E work is done. Never commit a real
 * plaintext admin password into a spec file; it lives only in the
 * gitignored .env.local.
 */
const baseHost = process.env.E2E_BASE_HOST ?? "127.0.0.1";
const basePort = process.env.E2E_BASE_PORT ?? "31594";
const hostHeader = process.env.E2E_HOST_HEADER ?? "platform.local";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  // Resource-constrained local cluster host: keep concurrency minimal so
  // the browser + real network calls don't compete with the cluster.
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: `http://${hostHeader}:${basePort}`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        launchOptions: {
          args: [`--host-resolver-rules=MAP ${hostHeader} ${baseHost}`],
        },
      },
    },
  ],
});
