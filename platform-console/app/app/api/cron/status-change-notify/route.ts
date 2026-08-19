import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { detectStatusChanges } from "@/lib/status-page";
import { listStatusSubscriptions, notifyStatusSubscriber } from "@/lib/status-subscriptions";

// Real, unattended poller endpoint a platform-wide CronJob hits on a
// schedule -- authenticated the SAME shared-secret-header pattern
// app/api/cron/retention-purge/route.ts and lib/scheduled-jobs.ts's
// cron routes already establish (one-time operator provisioning:
// `kubectl create secret generic platform-status-change-cron-secret
// --from-literal=secret=...` in the `platform-console` namespace, then
// setting STATUS_CHANGE_CRON_SECRET on the console's own Deployment).
// Checked BEFORE any session cookie so the CronJob's Pod (which carries
// no session) can reach this route at all.
//
// One platform-wide CronJob, matching retention-purge's own "single
// platform-wide purge, not per-org" shape -- status is itself a
// platform-wide, not per-org, concept (see lib/status-page.ts's
// COMPONENT_ROSTER).
function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.STATUS_CHANGE_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-status-change-cron-secret");
  return presented === expected;
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  if (!isCronAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const detection = await detectStatusChanges();

  if (!detection.reachable) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "status-change-cron",
      method: "POST",
      path: "/api/cron/status-change-notify",
      status: 200,
      requestId,
    });
    return NextResponse.json({
      reachable: false,
      changedComponentCount: 0,
      notified: 0,
    });
  }

  if (detection.changedComponents.length === 0) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "status-change-cron",
      method: "POST",
      path: "/api/cron/status-change-notify",
      status: 200,
      requestId,
    });
    return NextResponse.json({
      reachable: true,
      changedComponentCount: 0,
      notified: 0,
      snapshotWriteError: detection.snapshotWriteError,
    });
  }

  const subscriptionsResult = await listStatusSubscriptions();
  const subscriptions = subscriptionsResult.ok ? subscriptionsResult.data : [];

  const changedIds = new Set(detection.changedComponents.map((c) => c.id));
  const results = await Promise.all(
    subscriptions
      .filter((sub) => {
        if (!sub.componentFilter) return true; // no filter -> notified of every change
        return sub.componentFilter.some((id) => changedIds.has(id));
      })
      .map(async (sub) => {
        const relevant = sub.componentFilter
          ? detection.changedComponents.filter((c) => sub.componentFilter!.includes(c.id))
          : detection.changedComponents;
        return notifyStatusSubscriber(sub, relevant, detection.generatedAt);
      }),
  );

  const notified = results.filter((r) => r.ok).length;
  const failed = results.filter((r) => !r.ok);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: "status-change-cron",
    method: "POST",
    path: "/api/cron/status-change-notify",
    status: subscriptionsResult.ok ? 200 : 502,
    requestId,
  });

  return NextResponse.json({
    reachable: true,
    changedComponentCount: detection.changedComponents.length,
    changedComponents: detection.changedComponents.map((c) => ({ id: c.id, state: c.state })),
    subscriberCount: subscriptions.length,
    notified,
    failedDeliveries: failed.map((f) => ({ subscriptionId: f.subscriptionId, error: f.error })),
    snapshotWriteError: detection.snapshotWriteError,
    listSubscriptionsError: subscriptionsResult.ok ? null : subscriptionsResult.error,
  });
}
