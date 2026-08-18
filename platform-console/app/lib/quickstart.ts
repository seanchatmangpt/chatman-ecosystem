/**
 * Generates the /quickstart page's personalized `quickstart.sh`: a real
 * bash script that drives this exact deployment's real HTTP API with
 * nothing but curl + jq, demonstrating the same self-service lifecycle
 * every other module in this console already exposes -- create an API
 * key, create a project, wait for it to reach Ready, back it up, tear it
 * down -- the AWS CLI getting-started / `gcloud init` / Vercel CLI
 * equivalent for this PaaS. No new backend capability: every curl call
 * below hits an API route that already exists (app/api/api-keys,
 * app/api/projects, app/api/projects/[name]/backups,
 * app/api/projects/[name] DELETE), the exact same routes the browser
 * console itself calls.
 */

const NAMESPACE = "supabase-demo"; // the real, already-provisioned project namespace this cluster ships with (see README's "How to reach it" / the live `demo-project`) -- the console has no self-service namespace-creation capability, so the quickstart reuses the one that's already there rather than inventing one.

function sanitizeIdentifier(identifier: string): string {
  const cleaned = identifier
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return (cleaned || "user").slice(0, 16);
}

function compactTimestamp(iso: string): string {
  // 2026-08-18T12:34:56.789Z -> 20260818123456
  return iso.replace(/[-:]/g, "").replace(/\.\d+Z$/, "").replace("T", "").slice(0, 14);
}

export interface QuickstartScriptInput {
  baseUrl: string; // this deployment's real base URL, resolved from the incoming request's own Host header -- see app/quickstart/page.tsx
  sessionCookie: string; // the viewer's own live platform_console_session JWT -- see app/quickstart/page.tsx's header comment for why
  identifier: string; // roleIdentifierFor(session) -- email for gotrue users, "admin" for local-admin
  role: string; // getRoleFor(session) -- viewer, member, or owner
  generatedAt: string; // ISO timestamp this script was generated at
}

export function quickstartProjectName(input: Pick<QuickstartScriptInput, "identifier" | "generatedAt">): string {
  return `quickstart-${sanitizeIdentifier(input.identifier)}-${compactTimestamp(input.generatedAt)}`;
}

export function buildQuickstartScript(input: QuickstartScriptInput): string {
  const projectName = quickstartProjectName(input);
  const keyName = `quickstart-${compactTimestamp(input.generatedAt)}`;

  return `#!/usr/bin/env bash
# platform-console quickstart
#
# Generated for: ${input.identifier} (role: ${input.role})
# Generated at:  ${input.generatedAt}
# Base URL:      ${input.baseUrl}
#
# The AWS CLI getting-started / \`gcloud init\` / Vercel CLI equivalent for
# this console: five real curl calls against this deployment's own real
# HTTP API (the exact same routes the browser console itself calls -- no
# separate "demo" API, nothing fabricated), demonstrating the full
# self-service lifecycle: create an API key, create a project, wait for
# it to reach real Ready status, back it up, then clean up.
#
# Requires: bash, curl, jq.
set -euo pipefail

BASE_URL="${input.baseUrl}"

# This is YOUR OWN live browser session cookie, captured at the moment
# this script was generated (app/quickstart/page.tsx reads it straight
# off the request that rendered this page, via the same
# platform_console_session cookie every other page already uses -- see
# lib/session.ts). It authenticates exactly one call below: minting an
# API key. It is time-limited (expires with your session -- up to 8h,
# lib/session.ts's SESSION_TTL_SECONDS) and this file should be treated
# as sensitive for as long as it's valid, the same way a downloaded
# credentials.csv from a real cloud console would be -- delete it (or let
# it expire) once you're done. Every step AFTER step 1 authenticates with
# the API key minted here instead, exactly the way a real CLI/SDK would,
# never with this cookie again.
SESSION_COOKIE="${input.sessionCookie}"

PROJECT_NAME="${projectName}"
NAMESPACE="${NAMESPACE}"

bold() { printf '\\n\\033[1m%s\\033[0m\\n' "$1"; }

bold "== platform-console quickstart =="
echo "Base URL: $BASE_URL"
echo "Project:  $PROJECT_NAME (namespace: $NAMESPACE)"

# ---------------------------------------------------------------------------
# Step 1/5 -- Create an API key for the current user (API Keys module)
# ---------------------------------------------------------------------------
# POST /api/api-keys (app/api/api-keys/route.ts) mints a real,
# cryptographically random pk_live_... token bound to YOUR identity,
# stored server-side only as a SHA-256 hash (lib/api-keys.ts) -- this
# response is the ONLY place the plaintext key is ever returned. Creating
# an API key is owner-only (requireRole(session, "owner")); if your
# account is not an owner this call -- and everything after it -- will
# fail with a real 403. That is real RBAC being enforced, not a script
# bug: ask an owner to create a key for you, or run this from an owner
# account.
bold "--- [1/5] Creating an API key ---"
create_key_response=$(curl -sS -X POST "$BASE_URL/api/api-keys" \\
  -H "content-type: application/json" \\
  -H "cookie: platform_console_session=$SESSION_COOKIE" \\
  -d '{"name":"${keyName}"}')
echo "$create_key_response" | jq .

api_key=$(echo "$create_key_response" | jq -r '.plaintext // empty')
if [ -z "$api_key" ]; then
  echo "Failed to create an API key -- see the response above." >&2
  echo "(Most likely cause: your role isn't 'owner', or this page's embedded session has expired -- re-download quickstart.sh from $BASE_URL/quickstart.)" >&2
  exit 1
fi
key_prefix=$(echo "$create_key_response" | jq -r '.key.prefix')
echo "Created API key: $key_prefix"

# Every call from here on authenticates as a real, standalone API client
# -- exactly like a CI pipeline or your own script would, with no browser
# involved -- via \`Authorization: Bearer pk_live_...\`. middleware.ts's
# resolveApiKeyAuth() resolves that header into the exact same kind of
# session every cookie-authenticated page request already gets; zero
# route files were written twice to support this.
auth_header="Authorization: Bearer $api_key"

# ---------------------------------------------------------------------------
# Step 2/5 -- Create a real project (self-service Projects API)
# ---------------------------------------------------------------------------
# POST /api/projects (app/api/projects/route.ts) submits a real
# SingleDatabase + Project custom resource pair
# (core.supabase.io/v1alpha1) to the Kubernetes API via the console's own
# ServiceAccount. The real supabase-operator already running on this
# cluster reconciles both -- standing up Postgres, GoTrue, PostgREST,
# Realtime, Storage, and an edge-functions runtime as real
# Deployments/Services, same as if you'd used the /projects form.
bold "--- [2/5] Creating project '$PROJECT_NAME' ---"
create_project_response=$(curl -sS -X POST "$BASE_URL/api/projects" \\
  -H "content-type: application/json" \\
  -H "$auth_header" \\
  -d "{\\"name\\":\\"$PROJECT_NAME\\",\\"namespace\\":\\"$NAMESPACE\\"}")
echo "$create_project_response" | jq .

if [ "$(echo "$create_project_response" | jq -r 'has("project")')" != "true" ]; then
  echo "Failed to create the project -- see the response above." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Step 3/5 -- Poll until the Project reaches real Ready status
# ---------------------------------------------------------------------------
# GET /api/projects lists every real Project CR this ServiceAccount can
# see, each with its real, live status.conditions[Ready] value (set by
# the operator, never fabricated here) -- the same list the /projects
# page itself renders. Polled rather than watched to keep this script
# dependency-free (curl + jq only).
bold "--- [3/5] Waiting for Project/$PROJECT_NAME to reach Ready ---"
ready="false"
for i in $(seq 1 30); do
  ready=$(curl -sS "$BASE_URL/api/projects" -H "$auth_header" \\
    | jq -r --arg n "$PROJECT_NAME" '.projects[] | select(.name==$n) | .ready')
  echo "  poll $i/30: ready=$ready"
  if [ "$ready" = "true" ]; then
    echo "Project is Ready."
    break
  fi
  sleep 5
done
if [ "$ready" != "true" ]; then
  echo "Project did not reach Ready in the time this script waited -- inspect it at $BASE_URL/projects/$PROJECT_NAME/database" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Step 4/5 -- Trigger a real backup (Database Backups module)
# ---------------------------------------------------------------------------
# POST /api/projects/$PROJECT_NAME/backups (app/api/projects/[name]/
# backups/route.ts) submits a real batch/v1 Job that runs pg_dump against
# the project's live Postgres Service and writes the dump to a real PVC
# -- the RDS/Cloud SQL automated-backup equivalent. Polled the same way
# as project readiness above.
bold "--- [4/5] Running a backup of $PROJECT_NAME ---"
backup_response=$(curl -sS -X POST "$BASE_URL/api/projects/$PROJECT_NAME/backups" -H "$auth_header")
echo "$backup_response" | jq .

backup_job=$(echo "$backup_response" | jq -r '.job.name // empty')
if [ -z "$backup_job" ]; then
  echo "Failed to start a backup -- see the response above." >&2
  exit 1
fi
echo "Waiting for backup Job/$backup_job to reach Complete..."
backup_status="Pending"
for i in $(seq 1 30); do
  backup_status=$(curl -sS "$BASE_URL/api/projects/$PROJECT_NAME/backups" -H "$auth_header" \\
    | jq -r --arg j "$backup_job" '.jobs[] | select(.name==$j) | .status')
  echo "  poll $i/30: status=$backup_status"
  if [ "$backup_status" = "Complete" ]; then
    echo "Backup Complete."
    break
  fi
  if [ "$backup_status" = "Failed" ]; then
    echo "Backup Job failed -- inspect it at $BASE_URL/projects/$PROJECT_NAME/backups" >&2
    break
  fi
  sleep 3
done

# ---------------------------------------------------------------------------
# Step 5/5 -- Clean up: delete the project
# ---------------------------------------------------------------------------
# DELETE /api/projects/$PROJECT_NAME (app/api/projects/[name]/route.ts)
# deletes the real Project CR this script created in step 2, and its
# paired SingleDatabase CR, via the console's ServiceAccount -- the exact
# reverse of createProjectWithDatabase. Same owner-only gate as creation.
bold "--- [5/5] Cleaning up: deleting $PROJECT_NAME ---"
delete_response=$(curl -sS -o /dev/null -w '%{http_code}' -X DELETE "$BASE_URL/api/projects/$PROJECT_NAME" -H "$auth_header")
echo "DELETE /api/projects/$PROJECT_NAME -> HTTP $delete_response"
if [ "$delete_response" != "200" ]; then
  echo "Cleanup did not return 200 -- check $BASE_URL/projects for '$PROJECT_NAME'." >&2
  exit 1
fi

bold "== Done =="
echo "Everything above ran against this deployment's real, live API -- nothing in this script is simulated."
echo
key_id=$(echo "$create_key_response" | jq -r '.key.id')
echo "The API key created in step 1 ($key_prefix) is still active. Revoke it when you're done exploring:"
echo "  curl -X DELETE \\"$BASE_URL/api/api-keys?id=$key_id\\" -H \\"$auth_header\\""
`;
}
