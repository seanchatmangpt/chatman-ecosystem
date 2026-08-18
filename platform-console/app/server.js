/**
 * Custom Next.js server entrypoint -- replaces the auto-generated
 * `.next/standalone/server.js` this app used before this pass. The
 * standalone server has no hook for handling raw HTTP `Upgrade` requests
 * (no `server.on("upgrade", ...)` is reachable from outside it), and a
 * WebSocket-based real-time notification relay needs exactly that hook.
 * So this file does what every documented Next.js "custom server" does
 * (https://nextjs.org/docs/pages/building-your-application/configuring/custom-server):
 * `next({dev:false})` + `app.getRequestHandler()` for ordinary HTTP, plus
 * a real `http.Server` this module owns so it can also answer `Upgrade`
 * requests on `/ws/notifications`. Dockerfile now copies the FULL
 * `node_modules` (not `.next/standalone`'s pruned subset) into the runner
 * image so `ws`/`next`/`jose` are all present here -- see the Dockerfile's
 * own comment on that stage for the size/simplicity tradeoff.
 *
 * This is intentionally a plain CommonJS file, not a `.ts` module under
 * `lib/`: it runs as the literal process entrypoint (`node server.js`,
 * see Dockerfile CMD), before Next's own module graph / path-alias
 * resolution (`@/lib/...`) exists, so it cannot `import` the TypeScript
 * lib/ modules directly. The pieces it needs from lib/k8s.ts (in-cluster
 * ServiceAccount HTTPS client) and lib/session.ts (HS256 session cookie
 * verification via `jose`) are re-implemented here at the small scale
 * actually needed -- same real mechanism (same token/CA paths, same
 * AUTH_SECRET, same cookie name), just inlined because of the module-
 * system boundary, not duplicated business logic.
 *
 * ---------------------------------------------------------------------
 * The relay itself (Supabase Realtime -> this process -> browser clients)
 * ---------------------------------------------------------------------
 * One shared upstream Phoenix-channel WebSocket connects this pod to the
 * real, already-running `demo-project-realtime` service (confirmed live
 * via `kubectl logs`/`kubectl exec` before any of this was written -- see
 * evidence/control-evidence-bundle.json's
 * "realtime-notification-pushed-not-polled" control) and joins
 * `postgres_changes` on `platform_console.audit_log` INSERT (added to the
 * `supabase_realtime` publication with a real
 * `ALTER PUBLICATION ... ADD TABLE`, verified via `pg_publication_tables`).
 * Every browser that opens `wss://<host>/ws/notifications` with a valid
 * platform-console session cookie is added to a fan-out set; every real
 * postgres_changes push from Realtime is forwarded to all of them
 * verbatim (minus Realtime's own envelope) as soon as it arrives -- a
 * genuine server-initiated push, not a poll loop on either leg.
 */
const { createServer } = require("node:http");
const { parse } = require("node:url");
const fs = require("node:fs");
const https = require("node:https");
const next = require("next");
const { WebSocketServer, WebSocket } = require("ws");
const { jwtVerify } = require("jose");

const PORT = parseInt(process.env.PORT || "3000", 10);
const HOSTNAME = process.env.HOSTNAME || "0.0.0.0";
const SESSION_COOKIE_NAME = "platform_console_session";

const app = next({ dev: false, dir: __dirname });
const handle = app.getRequestHandler();

// ----------------------------------------------------------- session auth
// Deliberately just "is this a real, currently-valid platform-console
// session" (any authProvider, any role) -- not the owner-only gate
// GET /api/audit itself enforces. A live count/list of "an authenticated
// action just happened, by whom, what path, what status" is the same
// class of low-sensitivity signal every hyperscaler console's own
// notification bell shows to any signed-in operator; the full audit
// *log* page (actor/path substring search, pagination, raw rows) stays
// owner-gated exactly as before -- this bell is a notice, not that report.
async function verifySession(cookieHeader) {
  if (!cookieHeader) return null;
  const match = cookieHeader
    .split(";")
    .map((p) => p.trim())
    .find((p) => p.startsWith(`${SESSION_COOKIE_NAME}=`));
  if (!match) return null;
  const token = decodeURIComponent(match.slice(SESSION_COOKIE_NAME.length + 1));
  const secret = process.env.AUTH_SECRET;
  if (!secret || secret.length < 16) return null;
  try {
    const key = new TextEncoder().encode(secret);
    const { payload } = await jwtVerify(token, key, { algorithms: ["HS256"] });
    return typeof payload.sub === "string" ? payload : null;
  } catch {
    return null;
  }
}

// --------------------------------------------------- in-cluster k8s client
// Same real mechanism as lib/k8s.ts's readInClusterConfig/k8sRequest
// (in-cluster ServiceAccount token + CA bundle Kubernetes mounts
// automatically), reimplemented here because this file sits outside
// Next's TS module graph (see header comment). Used once, at relay
// startup, to resolve the real Realtime Service DNS name -- never
// hardcoded, so this keeps working if the operator ever renames/moves it.
const SA_DIR = "/var/run/secrets/kubernetes.io/serviceaccount";

function readInClusterConfig() {
  try {
    const tokenPath = `${SA_DIR}/token`;
    const caPath = `${SA_DIR}/ca.crt`;
    const host = process.env.KUBERNETES_SERVICE_HOST;
    const port = process.env.KUBERNETES_SERVICE_PORT || "443";
    if (!host || !fs.existsSync(tokenPath) || !fs.existsSync(caPath)) return null;
    return {
      token: fs.readFileSync(tokenPath, "utf8").trim(),
      ca: fs.readFileSync(caPath),
      host,
      port,
    };
  } catch {
    return null;
  }
}

function k8sRequest(path) {
  const cfg = readInClusterConfig();
  if (!cfg) return Promise.resolve({ ok: false, error: "not configured: no in-cluster ServiceAccount credentials" });
  return new Promise((resolve) => {
    const req = https.request(
      {
        host: cfg.host,
        port: cfg.port,
        path,
        method: "GET",
        ca: cfg.ca,
        headers: { Authorization: `Bearer ${cfg.token}` },
        timeout: 5000,
      },
      (res) => {
        let raw = "";
        res.on("data", (c) => (raw += c));
        res.on("end", () => {
          try {
            const data = JSON.parse(raw);
            if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
              resolve({ ok: true, data });
            } else {
              resolve({ ok: false, error: `k8s API ${path} -> HTTP ${res.statusCode}: ${raw.slice(0, 300)}` });
            }
          } catch (err) {
            resolve({ ok: false, error: `k8s API ${path}: invalid JSON response (${err.message})` });
          }
        });
      },
    );
    req.on("timeout", () => req.destroy(new Error("k8s API request timed out")));
    req.on("error", (err) => resolve({ ok: false, error: `k8s API ${path}: ${err.message}` }));
    req.end();
  });
}

// The one console-operational Supabase project this whole console treats
// as its own (same "demo-project" convention lib/audit-db.ts documents
// and justifies at length in its own header comment -- not repeated
// here). Its Realtime Service is discovered live by the
// `app.kubernetes.io/component=realtime` label (the same label
// lib/k8s.ts's getProjectDatabasePod already matches on for
// `component=database`), never a hardcoded Service name.
const REALTIME_PROJECT_NAME = "demo-project";

// The Realtime tenant this pod's audit-log channel joins under. NOT
// derived from the k8s Project name -- confirmed live via
// `kubectl exec ... psql -c "SELECT external_id FROM _realtime.tenants"`
// during this pass, this is supabase/realtime's own fixed self-host demo
// tenant (seeded by the image's `SEED_SELF_HOST=true` env var,
// independent of which Supabase Project k8s object exists), the same
// tenant every one of this cluster's `demo-project-realtime` pod's own
// startup logs already show ("Tenant set-up successfully"). Realtime
// resolves the tenant from the first dot-delimited label of the HTTP
// `Host` header (verified live: `Host: localhost` -> `external_id:
// localhost`; `Host: realtime-dev.<anything>` -> `external_id:
// realtime-dev`), which is why the upstream connection below sends an
// explicit synthetic Host header rather than relying on the Service's
// real cluster-DNS name.
const REALTIME_TENANT = "realtime-dev";
const REALTIME_HOST_HEADER = `${REALTIME_TENANT}.platform-console-relay.internal`;

async function resolveRealtimeWsUrl() {
  const projectsResult = await k8sRequest("/apis/core.supabase.io/v1alpha1/projects");
  if (!projectsResult.ok) throw new Error(projectsResult.error);
  const project = (projectsResult.data.items || []).find(
    (p) => p.metadata && p.metadata.name === REALTIME_PROJECT_NAME,
  );
  if (!project) throw new Error(`Supabase Project '${REALTIME_PROJECT_NAME}' not found`);
  const namespace = project.metadata.namespace;

  const servicesResult = await k8sRequest(`/api/v1/namespaces/${encodeURIComponent(namespace)}/services`);
  if (!servicesResult.ok) throw new Error(servicesResult.error);
  const svc = (servicesResult.data.items || []).find(
    (s) => s.metadata.labels && s.metadata.labels["app.kubernetes.io/component"] === "realtime",
  );
  if (!svc) throw new Error(`no Realtime Service found in namespace '${namespace}' (component=realtime)`);
  const port = (svc.spec.ports || []).find((p) => p.port) || { port: 4000 };
  const dns = `${svc.metadata.name}.${namespace}.svc.cluster.local`;
  return `ws://${dns}:${port.port}/socket/websocket?apikey=${encodeURIComponent(process.env.SUPABASE_SERVICE_ROLE_KEY || "")}&vsn=1.0.0`;
}

// --------------------------------------------------------------- fan-out
const browserClients = new Set();
let upstreamStatus = "connecting"; // "connecting" | "subscribed" | "error"
let upstreamLastError = null;

function broadcast(obj) {
  const msg = JSON.stringify(obj);
  for (const client of browserClients) {
    if (client.readyState === WebSocket.OPEN) client.send(msg);
  }
}

function connectUpstream() {
  if (!process.env.SUPABASE_SERVICE_ROLE_KEY) {
    upstreamStatus = "error";
    upstreamLastError = "SUPABASE_SERVICE_ROLE_KEY not configured";
    console.error(JSON.stringify({ realtimeRelayError: upstreamLastError }));
    return;
  }

  resolveRealtimeWsUrl()
    .then((wsUrl) => {
      const upstream = new WebSocket(wsUrl, { headers: { Host: REALTIME_HOST_HEADER } });
      let heartbeatTimer = null;
      let ref = 1;

      upstream.on("open", () => {
        upstream.send(
          JSON.stringify({
            topic: "realtime:platform-console-audit-log",
            event: "phx_join",
            payload: {
              config: {
                broadcast: { ack: false, self: false },
                presence: { key: "" },
                postgres_changes: [
                  { event: "INSERT", schema: "platform_console", table: "audit_log" },
                ],
              },
              access_token: process.env.SUPABASE_SERVICE_ROLE_KEY,
            },
            ref: String(ref++),
          }),
        );
        heartbeatTimer = setInterval(() => {
          if (upstream.readyState === WebSocket.OPEN) {
            upstream.send(JSON.stringify({ topic: "phoenix", event: "heartbeat", payload: {}, ref: String(ref++) }));
          }
        }, 25000);
      });

      upstream.on("message", (raw) => {
        let msg;
        try {
          msg = JSON.parse(raw.toString());
        } catch {
          return;
        }
        if (msg.event === "system" && msg.payload && msg.payload.status === "ok") {
          upstreamStatus = "subscribed";
          upstreamLastError = null;
          console.log(JSON.stringify({ realtimeRelay: "subscribed", channel: msg.payload.channel }));
          broadcast({ type: "connection.status", status: "subscribed" });
        } else if (msg.event === "postgres_changes" && msg.payload && msg.payload.data) {
          const data = msg.payload.data;
          console.log(
            JSON.stringify({
              realtimeRelayPush: true,
              table: data.table,
              type: data.type,
              recordId: data.record ? data.record.id : null,
            }),
          );
          broadcast({
            type: "audit_log.insert",
            record: data.record,
            errors: data.errors,
            commitTimestamp: data.commit_timestamp,
          });
        } else if (msg.event === "phx_reply" && msg.payload && msg.payload.status === "error") {
          upstreamStatus = "error";
          upstreamLastError = JSON.stringify(msg.payload.response);
          console.error(JSON.stringify({ realtimeRelayJoinError: msg.payload.response }));
        }
      });

      upstream.on("close", () => {
        if (heartbeatTimer) clearInterval(heartbeatTimer);
        upstreamStatus = "error";
        upstreamLastError = "upstream Realtime connection closed";
        broadcast({ type: "connection.status", status: "reconnecting" });
        setTimeout(connectUpstream, 3000);
      });

      upstream.on("error", (err) => {
        upstreamLastError = err.message;
        console.error(JSON.stringify({ realtimeRelayUpstreamError: err.message }));
      });
    })
    .catch((err) => {
      upstreamStatus = "error";
      upstreamLastError = err.message;
      console.error(JSON.stringify({ realtimeRelayResolveError: err.message }));
      setTimeout(connectUpstream, 5000);
    });
}

// --------------------------------------------------------------- HTTP/WS
app.prepare().then(() => {
  const server = createServer((req, res) => {
    handle(req, res, parse(req.url, true));
  });

  const wss = new WebSocketServer({ noServer: true });

  server.on("upgrade", (req, socket, head) => {
    const { pathname } = parse(req.url);
    if (pathname !== "/ws/notifications") {
      socket.destroy();
      return;
    }
    verifySession(req.headers.cookie).then((session) => {
      if (!session) {
        socket.write("HTTP/1.1 401 Unauthorized\r\nConnection: close\r\n\r\n");
        socket.destroy();
        return;
      }
      wss.handleUpgrade(req, socket, head, (ws) => {
        browserClients.add(ws);
        ws.send(
          JSON.stringify({
            type: "connection.status",
            status: upstreamStatus,
            error: upstreamLastError,
          }),
        );
        ws.on("close", () => browserClients.delete(ws));
        ws.on("error", () => browserClients.delete(ws));
      });
    });
  });

  server.listen(PORT, HOSTNAME, () => {
    console.log(JSON.stringify({ serverReady: true, port: PORT, hostname: HOSTNAME }));
    connectUpstream();
  });
});
