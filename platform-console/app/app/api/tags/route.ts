import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getRoleFor, requireRole } from "@/lib/authz";
import {
  applyTag,
  fixedRefFor,
  getResourceTags,
  listResourcesByTag,
  minRoleForTagging,
  removeTag,
  type TaggableResourceType,
} from "@/lib/tags";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do. Same pattern as app/api/search/route.ts and
// app/api/feature-flags/route.ts.

const TAGGABLE_TYPES: TaggableResourceType[] = [
  "service",
  "project",
  "cronjob",
  "feature-flags",
  "webhooks",
];

function isTaggableResourceType(value: unknown): value is TaggableResourceType {
  return typeof value === "string" && (TAGGABLE_TYPES as string[]).includes(value);
}

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

/**
 * GET /api/tags
 *  - ?key=&value=          -> real cross-resource "browse by tag" lookup
 *                              (lib/tags.ts's listResourcesByTag), role-
 *                              filtered exactly like GET /api/search.
 *  - ?resourceType=&namespace=&name= -> real single-object tag read
 *                              (getResourceTags), used by the tag-editor
 *                              widgets on Service Discovery/Projects to
 *                              show one resource's current tags.
 */
export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;
  const params = request.nextUrl.searchParams;

  const resourceType = params.get("resourceType");
  if (resourceType) {
    if (!isTaggableResourceType(resourceType)) {
      return NextResponse.json({ error: `unknown resourceType "${resourceType}"` }, { status: 400 });
    }
    const namespace = params.get("namespace") ?? "";
    const name = params.get("name") ?? "";
    if ((!namespace || !name) && resourceType !== "feature-flags" && resourceType !== "webhooks") {
      return NextResponse.json({ error: "namespace and name are required" }, { status: 400 });
    }
    const ref =
      resourceType === "feature-flags" || resourceType === "webhooks"
        ? fixedRefFor(resourceType)
        : { namespace, name };

    const result = await getResourceTags(resourceType, ref);
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/tags",
      status: result.ok ? 200 : 502,
      requestId,
    });
    if (!result.ok) return NextResponse.json({ error: result.error }, { status: 502 });
    return NextResponse.json({ tags: result.data });
  }

  const key = (params.get("key") ?? "").trim();
  const value = (params.get("value") ?? "").trim();
  if (!key || !value) {
    return NextResponse.json({ resources: [] });
  }

  const role = await getRoleFor(session);
  const resources = await listResourcesByTag(key, value, role);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/tags",
    status: 200,
    requestId,
  });

  return NextResponse.json({ resources });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const body = await request.json().catch(() => null);
  const resourceType = body?.resourceType;
  if (!isTaggableResourceType(resourceType)) {
    return NextResponse.json({ error: `unknown resourceType "${resourceType}"` }, { status: 400 });
  }

  // Real app-level RBAC boundary: applying a tag needs at least the same
  // minimum role Global Search's own CATEGORY_MIN_ROLE requires to SEE
  // this category (raised to "member" as a floor for every other
  // category) -- see lib/tags.ts's minRoleForTagging.
  const access = await requireRole(session, minRoleForTagging(resourceType));
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/tags",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const key = typeof body?.key === "string" ? body.key.trim() : "";
  const value = typeof body?.value === "string" ? body.value.trim() : "";
  const namespace = typeof body?.namespace === "string" ? body.namespace : "";
  const name = typeof body?.name === "string" ? body.name : "";

  const ref =
    resourceType === "feature-flags" || resourceType === "webhooks"
      ? fixedRefFor(resourceType)
      : { namespace, name };

  if (resourceType !== "feature-flags" && resourceType !== "webhooks" && (!namespace || !name)) {
    return NextResponse.json({ error: "namespace and name are required" }, { status: 400 });
  }

  const result = await applyTag(resourceType, ref, key, value);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/tags",
    status: result.ok ? 200 : result.error.includes("required") || result.error.includes("Kubernetes") ? 400 : 502,
    requestId,
  });

  if (!result.ok) {
    const clientError = result.error.includes("required") || result.error.includes("Kubernetes");
    return NextResponse.json({ error: result.error }, { status: clientError ? 400 : 502 });
  }
  return NextResponse.json({ tags: result.data });
}

export async function DELETE(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const params = request.nextUrl.searchParams;
  const resourceType = params.get("resourceType");
  if (!isTaggableResourceType(resourceType)) {
    return NextResponse.json({ error: `unknown resourceType "${resourceType}"` }, { status: 400 });
  }

  const access = await requireRole(session, minRoleForTagging(resourceType));
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: "/api/tags",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const namespace = params.get("namespace") ?? "";
  const name = params.get("name") ?? "";
  const key = (params.get("key") ?? "").trim();
  if (!key) {
    return NextResponse.json({ error: "key is required" }, { status: 400 });
  }
  if (resourceType !== "feature-flags" && resourceType !== "webhooks" && (!namespace || !name)) {
    return NextResponse.json({ error: "namespace and name are required" }, { status: 400 });
  }

  const ref =
    resourceType === "feature-flags" || resourceType === "webhooks"
      ? fixedRefFor(resourceType)
      : { namespace, name };

  const result = await removeTag(resourceType, ref, key);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: "/api/tags",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) return NextResponse.json({ error: result.error }, { status: 502 });
  return NextResponse.json({ tags: result.data });
}
