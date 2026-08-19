import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { getProject, getProjectStorageService } from "@/lib/k8s";
import { fetchStorageBuckets } from "@/lib/storage-api";
import {
  DEFAULT_TTL_SECONDS,
  MAX_TTL_SECONDS,
  MIN_TTL_SECONDS,
  signStorageDownloadToken,
} from "@/lib/storage-signed-url";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Project-scoped, resolved live via getProjectStorageService -- same
// component=storage/instance=<project.name> Service lookup
// app/projects/[name]/storage/page.tsx already renders inline (now shared
// via lib/k8s.ts rather than duplicated a third time). No project name
// ever appears in this file as a literal.
//
// POST mints one real, time-boxed HMAC-signed download URL for one object
// in one bucket -- the Content/IP protection primitive this route exists
// for (control: storage-signed-url-expiry-enforced). Member+ (not viewer):
// minting a link that lets an unreleased asset leave this console's own
// auth boundary is a write-class action, same reasoning every other
// mutating route in this console applies via requireRole.
//
// GET lists the real buckets available to sign against -- read-only,
// viewer-level, same fetchStorageBuckets call the /storage page itself
// already makes, exposed here too so the signing UI doesn't need a second
// server round trip through the page.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const { name } = await params;
  const projectResult = await getProject(name);
  if (!projectResult.ok) {
    return NextResponse.json({ error: projectResult.error }, { status: 502 });
  }
  if (!projectResult.data) {
    return NextResponse.json({ error: `project '${name}' not found` }, { status: 404 });
  }

  const svcResult = await getProjectStorageService(projectResult.data);
  if (!svcResult.ok) {
    return NextResponse.json({ error: svcResult.error }, { status: 502 });
  }
  if (!svcResult.data) {
    return NextResponse.json(
      { error: `no storage Service found for project '${name}'` },
      { status: 404 },
    );
  }

  const bucketsResult = await fetchStorageBuckets(svcResult.data.dns, svcResult.data.port);
  if (!bucketsResult.ok) {
    if (bucketsResult.notConfigured) {
      return NextResponse.json({ error: "storage service-role key not configured" }, { status: 501 });
    }
    return NextResponse.json({ error: bucketsResult.error }, { status: 502 });
  }
  return NextResponse.json({ buckets: bucketsResult.bucketNames });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;
  const { name } = await params;

  const access = await requireRole(session, "member");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/projects/${name}/storage (sign)`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = (await request.json().catch(() => ({}))) as Record<string, unknown>;
  const bucket = typeof body?.bucket === "string" ? body.bucket.trim() : "";
  const objectPath = typeof body?.path === "string" ? body.path.trim().replace(/^\/+/, "") : "";
  const ttlSecondsRaw = typeof body?.ttlSeconds === "number" ? body.ttlSeconds : DEFAULT_TTL_SECONDS;

  if (!bucket || !objectPath) {
    return NextResponse.json({ error: "bucket and path are required" }, { status: 400 });
  }

  const projectResult = await getProject(name);
  if (!projectResult.ok) {
    return NextResponse.json({ error: projectResult.error }, { status: 502 });
  }
  if (!projectResult.data) {
    return NextResponse.json({ error: `project '${name}' not found` }, { status: 404 });
  }

  const svcResult = await getProjectStorageService(projectResult.data);
  if (!svcResult.ok) {
    return NextResponse.json({ error: svcResult.error }, { status: 502 });
  }
  if (!svcResult.data) {
    return NextResponse.json(
      { error: `no storage Service found for project '${name}'` },
      { status: 404 },
    );
  }

  const identifier = roleIdentifierFor(session);
  const signed = signStorageDownloadToken(name, bucket, objectPath, identifier, ttlSecondsRaw);
  const downloadUrl = `/api/projects/${encodeURIComponent(name)}/storage/download?token=${encodeURIComponent(signed.token)}`;

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/projects/${name}/storage (sign: ${bucket}/${objectPath})`,
    status: 201,
    requestId,
  });

  return NextResponse.json(
    {
      url: downloadUrl,
      expiresAt: signed.expiresAt,
      ttlSecondsRange: { min: MIN_TTL_SECONDS, max: MAX_TTL_SECONDS },
    },
    { status: 201 },
  );
}
