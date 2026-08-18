/**
 * Background poller that turns two of this console's already-real
 * observation loops into real webhook triggers (plus the third real
 * trigger point, "project.created", which fires synchronously from the
 * createProjectWithDatabase success path in app/api/projects/route.ts
 * and needs no polling at all):
 *
 *  - "backup.completed": polls the exact same real `batch/v1` Jobs
 *    `createBackupJob` (lib/k8s.ts) creates, in the one namespace the
 *    `platform-console-backups` Role actually grants `batch/jobs`
 *    get/list on (`supabase-demo` -- see k8s/paas-rbac.yaml), and fires
 *    once per Job the moment its status FIRST reaches
 *    `status.succeeded >= 1`.
 *  - "alert.firing": polls the exact same Alertmanager `/api/v2/alerts`
 *    `lib/alertmanager.ts`'s `queryAlerts` already reads for the
 *    `/alerts` page, and fires once per alert fingerprint the moment it
 *    FIRST transitions into `alertState(...) === "firing"`.
 *
 * Both are tracked by an in-memory `Set` of already-notified
 * job-names/fingerprints so anything already Complete/firing before this
 * poller's first tick is a baseline, never replayed as a false "new"
 * delivery on process start.
 *
 * A real in-process interval, not a cron/queue system -- appropriate for
 * this console's deployment shape. `platform-console-gateway` runs 2
 * replicas; each replica independently polls and independently
 * delivers, so a subscriber may see up to one duplicate delivery per
 * real event across a 2-replica rollout. Real webhook consumers are
 * expected to dedupe on the `x-platform-webhook-delivery` id, the same
 * idempotency-key convention GitHub/Stripe receivers already follow --
 * disclosed here rather than papered over with a fabricated
 * single-leader-election step this console does not actually have.
 */
import { hasClusterCredentials, listJobs } from "@/lib/k8s";
import { alertState, queryAlerts } from "@/lib/alertmanager";
import { deliverWebhookEvent } from "@/lib/webhooks";

const POLL_INTERVAL_MS = 10_000;

// The only namespace platform-console-backups (k8s/paas-rbac.yaml)
// grants batch/jobs get/list/create in -- matches lib/k8s.ts's own
// createBackupJob/listJobs callers, never a guess.
const BACKUPS_NAMESPACE = "supabase-demo";
const BACKUPS_LABEL_SELECTOR = "app=platform-backups";

let started = false;
let firstBackupsTick = true;
let firstAlertsTick = true;
const notifiedCompletedJobNames = new Set<string>();
const notifiedFiringFingerprints = new Set<string>();

async function pollBackupCompletions(): Promise<void> {
  const result = await listJobs(BACKUPS_NAMESPACE, BACKUPS_LABEL_SELECTOR);
  if (!result.ok) {
    console.error(`[webhook-poller] listJobs(${BACKUPS_NAMESPACE}) failed: ${result.error}`);
    return;
  }

  for (const job of result.data) {
    if (job.status !== "Complete") continue;
    if (notifiedCompletedJobNames.has(job.name)) continue;
    notifiedCompletedJobNames.add(job.name);

    // First tick after process start establishes the baseline of
    // already-complete Jobs -- these were not caused by anything that
    // happened while a subscriber was listening, so they are not
    // delivered as "new" events.
    if (firstBackupsTick) continue;

    await deliverWebhookEvent("backup.completed", {
      jobName: job.name,
      namespace: job.namespace,
      startTime: job.startTime,
      completionTime: job.completionTime,
      durationSeconds: job.durationSeconds,
    });
  }
  firstBackupsTick = false;
}

async function pollAlertFirings(): Promise<void> {
  const result = await queryAlerts();
  if (!result.ok) {
    console.error(`[webhook-poller] queryAlerts failed: ${result.error}`);
    return;
  }

  const currentlyFiring = new Set<string>();
  for (const alert of result.data) {
    if (alertState(alert) !== "firing") continue;
    currentlyFiring.add(alert.fingerprint);
    if (notifiedFiringFingerprints.has(alert.fingerprint)) continue;
    notifiedFiringFingerprints.add(alert.fingerprint);

    if (firstAlertsTick) continue; // baseline -- see pollBackupCompletions

    await deliverWebhookEvent("alert.firing", {
      fingerprint: alert.fingerprint,
      labels: alert.labels,
      annotations: alert.annotations,
      startsAt: alert.startsAt,
    });
  }

  // An alert that stopped firing is forgotten so a future re-fire (a
  // genuinely new incident from an operator's perspective) is delivered
  // again rather than permanently suppressed.
  for (const fingerprint of notifiedFiringFingerprints) {
    if (!currentlyFiring.has(fingerprint)) notifiedFiringFingerprints.delete(fingerprint);
  }
  firstAlertsTick = false;
}

async function tick(): Promise<void> {
  if (!hasClusterCredentials()) return; // local dev / build -- nothing to poll
  await Promise.all([pollBackupCompletions(), pollAlertFirings()]);
}

/**
 * Starts the poller exactly once per process. Idempotent -- safe to call
 * from instrumentation.ts's `register()`, which Next.js itself guards to
 * run once per server process, but this guard also protects against any
 * accidental second import.
 */
export function startWebhookPoller(): void {
  if (started) return;
  started = true;
  void tick();
  setInterval(() => {
    void tick();
  }, POLL_INTERVAL_MS);
}
