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

// ------------------------------------------------------- Container Exec
//
// Real hyperscaler-PaaS-style browser-based shell access (AWS Systems
// Manager Session Manager / GCP Cloud Shell / Azure Cloud Shell "run a
// command in a running instance/pod" equivalent) -- the most sensitive
// capability in this console, so `/ws/exec` gets every layer of
// defense-in-depth `/ws/notifications` above has PLUS two more: a
// per-request app-level ROLE check (owner-only, not just "any valid
// session"), and a fixed COMMAND ALLOWLIST resolved and validated before
// this process ever opens a WebSocket to the k8s API -- an unrecognized
// commandId, non-owner session, or non-allowlisted namespace never
// reaches the k8s API at all (openExecRelay below, which is the only
// function that ever opens the upstream k8s WebSocket, is only ever
// called AFTER every one of those checks has already passed).
//
// lib/container-exec.ts is the source of truth for the command allowlist
// and the namespace allowlist (used by app/app/api/exec/route.ts's
// GET/POST handlers, which run inside Next's own module graph) -- both
// are mirrored here, small and disclosed, for the exact same reason
// server.js's header comment already gives for duplicating
// lib/k8s.ts/lib/session.ts's pieces: this file sits outside Next's TS
// module graph and cannot `import` a `@/lib/...` module directly. Keep
// both copies in sync by hand; this comment and lib/container-exec.ts's
// own header comment each point at the other.
const EXEC_NAMESPACES = ["autofde-lab", "gymact", "ggen", "ggen-marketplace", "supabase-demo", "platform-console"];

const ALLOWED_EXEC_COMMANDS = {
  "cat-facts": ["cat", "/app/facts.json"],
  echo: ["echo", "platform-console container-exec diagnostic"],
  env: ["env"],
  "ls-app": ["ls", "-la", "/app"],
};

function resolveExecCommand(commandId) {
  return Object.prototype.hasOwnProperty.call(ALLOWED_EXEC_COMMANDS, commandId)
    ? ALLOWED_EXEC_COMMANDS[commandId]
    : null;
}

// ------------------------------------------------- Application-level RBAC
//
// Mirrors lib/authz.ts's `getRoleFor` -- same real
// `platform-console-org-roles` ConfigMap, same identifier/encoding
// convention, same fail-closed defaults (local-admin -> owner,
// everyone else -> viewer, unless the ConfigMap has an explicit real
// entry). Duplicated here for the same module-boundary reason as
// everything else in this section; lib/authz.ts remains the source of
// truth every other route in the app actually runs through.
const ORG_ROLES_NAMESPACE = "platform-console";
const ORG_ROLES_CONFIGMAP = "platform-console-org-roles";

function encodeIdentifierKey(identifier) {
  return identifier.replace(/[^-._a-zA-Z0-9]/g, (ch) => `-x${ch.charCodeAt(0).toString(16)}-`);
}

function roleIdentifierFor(session) {
  return session.authProvider === "gotrue" || session.authProvider === "oidc-external"
    ? session.email
    : session.sub;
}

async function resolveRoleFor(session) {
  if (session.authProvider === "api-key") {
    return session.boundRole === "viewer" || session.boundRole === "member" || session.boundRole === "owner"
      ? session.boundRole
      : "viewer";
  }
  const identifier = roleIdentifierFor(session);
  const key = encodeIdentifierKey(String(identifier));
  const result = await k8sRequest(
    `/api/v1/namespaces/${encodeURIComponent(ORG_ROLES_NAMESPACE)}/configmaps/${encodeURIComponent(ORG_ROLES_CONFIGMAP)}`,
  );
  if (result.ok && result.data && result.data.data && typeof result.data.data[key] === "string") {
    const role = result.data.data[key];
    if (role === "viewer" || role === "member" || role === "owner") return role;
  }
  return session.authProvider === "local-admin" ? "owner" : "viewer";
}

// --------------------------------------------------- real k8s exec relay
//
// Opens a real WebSocket to the pod's exec subresource (the same
// mechanism lib/container-exec.ts's execAllowedCommand uses -- see that
// file's header comment for the wire-protocol/subprotocol details and
// the live confirmation that this cluster's real v1.34 API server
// answers a GET-upgraded WebSocket exec request, and that it evaluates
// the "get" verb for it, not just "create") using this pod's own
// in-cluster ServiceAccount token/CA (readInClusterConfig above -- the
// exact same credentials k8sRequest already uses for every other real
// k8s API call in this file), and relays every real stdout/stderr/status
// frame to the browser's own `/ws/exec` socket as it arrives -- a real,
// live, per-byte relay, not a buffered request/response.
const EXEC_SUBPROTOCOL = "v4.channel.k8s.io";

function openExecRelay(browserWs, namespace, pod, container, command) {
  const cfg = readInClusterConfig();
  if (!cfg) {
    browserWs.send(JSON.stringify({ type: "error", error: "not configured: no in-cluster ServiceAccount credentials" }));
    browserWs.close();
    return;
  }

  const params = new URLSearchParams();
  params.set("container", container);
  params.set("stdout", "true");
  params.set("stderr", "true");
  params.set("stdin", "false");
  params.set("tty", "false");
  for (const token of command) params.append("command", token);
  const path = `/api/v1/namespaces/${encodeURIComponent(namespace)}/pods/${encodeURIComponent(pod)}/exec?${params.toString()}`;
  const upstreamUrl = `wss://${cfg.host}:${cfg.port}${path}`;

  const upstream = new WebSocket(upstreamUrl, [EXEC_SUBPROTOCOL], {
    ca: cfg.ca,
    headers: { Authorization: `Bearer ${cfg.token}` },
    rejectUnauthorized: true,
  });

  upstream.on("open", () => {
    browserWs.send(JSON.stringify({ type: "connected" }));
  });

  upstream.on("unexpected-response", (_req, res) => {
    let body = "";
    res.on("data", (chunk) => (body += chunk));
    res.on("end", () => {
      browserWs.send(
        JSON.stringify({ type: "error", error: `exec upgrade rejected: HTTP ${res.statusCode} ${body.slice(0, 500)}` }),
      );
      browserWs.close();
    });
  });

  upstream.on("message", (data) => {
    if (data.length === 0) return;
    const channel = data[0];
    const payload = data.subarray(1).toString("utf8");
    if (channel === 1) browserWs.send(JSON.stringify({ type: "stdout", data: payload }));
    else if (channel === 2) browserWs.send(JSON.stringify({ type: "stderr", data: payload }));
    else if (channel === 3) browserWs.send(JSON.stringify({ type: "status", data: payload }));
  });

  upstream.on("close", () => {
    if (browserWs.readyState === WebSocket.OPEN) {
      browserWs.send(JSON.stringify({ type: "closed" }));
      browserWs.close();
    }
  });

  upstream.on("error", (err) => {
    browserWs.send(JSON.stringify({ type: "error", error: `exec WebSocket error: ${err.message}` }));
    browserWs.close();
  });

  browserWs.on("close", () => {
    if (upstream.readyState === WebSocket.OPEN || upstream.readyState === WebSocket.CONNECTING) {
      upstream.terminate();
    }
  });
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
  const execWss = new WebSocketServer({ noServer: true });

  server.on("upgrade", (req, socket, head) => {
    const { pathname, query } = parse(req.url, true);

    if (pathname === "/ws/notifications") {
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
      return;
    }

    if (pathname === "/ws/exec") {
      const namespace = typeof query.namespace === "string" ? query.namespace : "";
      const pod = typeof query.pod === "string" ? query.pod : "";
      const container = typeof query.container === "string" ? query.container : "";
      const commandId = typeof query.commandId === "string" ? query.commandId : "";

      verifySession(req.headers.cookie).then(async (session) => {
        if (!session) {
          console.log(JSON.stringify({ execAudit: true, actor: "anonymous", namespace, pod, commandId, status: 401 }));
          socket.write("HTTP/1.1 401 Unauthorized\r\nConnection: close\r\n\r\n");
          socket.destroy();
          return;
        }

        // Real app-level RBAC boundary: owner-only. Checked BEFORE the
        // command allowlist / k8s connection below -- a non-owner session
        // never even learns whether its commandId would have resolved.
        const role = await resolveRoleFor(session);
        if (role !== "owner") {
          console.log(
            JSON.stringify({ execAudit: true, actor: roleIdentifierFor(session), role, namespace, pod, commandId, status: 403 }),
          );
          socket.write("HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n");
          socket.destroy();
          return;
        }

        // Real security boundary: namespace + commandId are both resolved
        // against fixed, server-side allowlists here, BEFORE any upgrade
        // to the browser socket and BEFORE any connection to the k8s API
        // is attempted. Anything outside either allowlist is refused right
        // here -- there is no code path from an unrecognized commandId to
        // a real k8s exec WebSocket.
        if (!EXEC_NAMESPACES.includes(namespace) || !pod || !container) {
          console.log(
            JSON.stringify({ execAudit: true, actor: roleIdentifierFor(session), role, namespace, pod, commandId, status: 400, reason: "invalid namespace/pod/container" }),
          );
          socket.write("HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n");
          socket.destroy();
          return;
        }
        const command = resolveExecCommand(commandId);
        if (!command) {
          console.log(
            JSON.stringify({ execAudit: true, actor: roleIdentifierFor(session), role, namespace, pod, commandId, status: 400, reason: "commandId not on allowlist -- rejected before any k8s API call" }),
          );
          socket.write("HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n");
          socket.destroy();
          return;
        }

        execWss.handleUpgrade(req, socket, head, (ws) => {
          console.log(
            JSON.stringify({ execAudit: true, actor: roleIdentifierFor(session), role, namespace, pod, container, commandId, status: 200 }),
          );
          openExecRelay(ws, namespace, pod, container, command);
        });
      });
      return;
    }

    socket.destroy();
  });

  server.listen(PORT, HOSTNAME, () => {
    console.log(JSON.stringify({ serverReady: true, port: PORT, hostname: HOSTNAME }));
    connectUpstream();
  });
});
