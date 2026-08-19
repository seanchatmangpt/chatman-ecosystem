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
 *  - "budget.threshold_crossed": calls `lib/budget-alerts.ts`'s
 *    `checkBudgets()`, which itself re-runs the exact same
 *    `lib/invoice-preview.ts` Prometheus queries `/billing` and `/usage`
 *    already use, compares against each namespace's operator-configured
 *    threshold, and fires once per namespace+metric the moment usage
 *    FIRST crosses it -- deduped by a real "already alerted" marker
 *    persisted in `budget-alerts.ts`'s own ConfigMap (durable across
 *    restarts, unlike the two in-memory Sets below), and un-marked again
 *    the moment usage drops back under threshold so a later re-crossing
 *    fires again.
 *
 * The first two are tracked by an in-memory `Set` of already-notified
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
import { checkBudgets } from "@/lib/budget-alerts";
import { checkCostAnomalies } from "@/lib/cost-anomaly";
import { checkQuotaEnforcement } from "@/lib/quota-enforcement";
import { reconcilePlanState } from "@/lib/plan-state";
import { recomputeAllOverageEstimates } from "@/lib/overage-billing";
import { deliverWebhookEvent } from "@/lib/webhooks";

const POLL_INTERVAL_MS = 10_000;

// The only namespace platform-console-backups (k8s/paas-rbac.yaml)
// grants batch/jobs get/list/create in -- matches lib/k8s.ts's own
// createBackupJob/listJobs callers, never a guess.
const BACKUPS_NAMESPACE = "supabase-demo";
const BACKUPS_LABEL_SELECTOR = "app=platform-backups";

// Same platform-namespace roster lib/budget-alerts.ts's own /api route and
// app/cost/page.tsx already use -- the fixed set of namespaces this
// cluster actually meters, never a namespace list derived from an
// unvalidated source.
const COST_ANOMALY_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

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

/**
 * checkBudgets() is the only writer of budget-alerts.ts's `alerted.*`
 * dedup markers -- calling it here, once per real 10s tick, is what makes
 * "fire once per crossing, not once per tick" real rather than aspirational.
 * A namespace with no threshold configured costs nothing (checkBudgets
 * short-circuits to an empty crossings list); a namespace whose real
 * Prometheus query fails this tick is skipped, never fired on stale data.
 */
async function pollBudgetThresholds(): Promise<void> {
  const result = await checkBudgets();
  if (!result.ok) {
    console.error(`[webhook-poller] checkBudgets failed: ${result.error}`);
    return;
  }
  for (const crossing of result.data) {
    await deliverWebhookEvent("budget.threshold_crossed", {
      namespace: crossing.namespace,
      metric: crossing.metric,
      threshold: crossing.threshold,
      currentValue: crossing.currentValue,
      crossedAt: crossing.crossedAt,
    });
  }
}

/**
 * checkCostAnomalies() is the only writer of lib/cost-anomaly.ts's
 * `state.*` EWMA-baseline keys -- calling it here, once per real 10s tick,
 * is what makes "flag once per genuine new anomaly, not once per tick"
 * real, mirroring pollBudgetThresholds's exact same reasoning. Distinct
 * signal from budget-alerts: this fires on a namespace's spend suddenly
 * deviating from ITS OWN trailing baseline, even while comfortably under
 * any fixed dollar threshold an operator configured (or configured none at
 * all).
 */
async function pollCostAnomalies(): Promise<void> {
  const result = await checkCostAnomalies(COST_ANOMALY_NAMESPACES);
  if (!result.ok) {
    console.error(`[webhook-poller] checkCostAnomalies failed: ${result.error}`);
    return;
  }
  for (const event of result.data) {
    await deliverWebhookEvent("cost.anomaly_detected", {
      namespace: event.namespace,
      baselineSpend: event.baselineSpend,
      currentSpend: event.currentSpend,
      deviationPct: event.deviationPct,
      deviationThresholdPct: event.deviationThresholdPct,
      detectedAt: event.detectedAt,
    });
  }
}

/**
 * checkQuotaEnforcement() is the only writer of quota-enforcement.ts's
 * `enforced.*` dedup markers AND the only caller of its real
 * scale-to-0/annotate actions -- calling it here, once per real 10s
 * tick, is what makes a namespace actually get throttled on its own,
 * with no human clicking anything, rather than only ever showing a
 * percentage on a dashboard. A namespace with no threshold configured
 * costs nothing (checkQuotaEnforcement short-circuits to an empty
 * actions list); a namespace whose real usage query fails this tick is
 * skipped, never enforced on stale data.
 */
async function pollQuotaEnforcement(): Promise<void> {
  const result = await checkQuotaEnforcement();
  if (!result.ok) {
    console.error(`[webhook-poller] checkQuotaEnforcement failed: ${result.error}`);
    return;
  }
  for (const action of result.data) {
    await deliverWebhookEvent("quota.enforcement_triggered", {
      namespace: action.namespace,
      targetDeployment: action.targetDeployment,
      cpuPercent: action.cpuPercent,
      memoryPercent: action.memoryPercent,
      thresholdPercent: action.thresholdPercent,
      enforcedAt: action.enforcedAt,
    });
  }
}

/**
 * reconcilePlanState() (lib/plan-state.ts) is the only writer of that
 * module's `enforced.*`/`saved-hard.*` markers AND the only caller of its
 * real ResourceQuota-patch actions -- calling it here, once per real 10s
 * tick, is what makes a namespace whose plan state has gone `past_due`/
 * `suspended` actually get its ResourceQuota suspended on its own (and
 * restored on its own once plan state returns to `active`), with no
 * human clicking anything. A namespace with no plan state recorded costs
 * nothing (reconcilePlanState short-circuits to an empty actions list).
 */
async function pollPlanState(): Promise<void> {
  const result = await reconcilePlanState();
  if (!result.ok) {
    console.error(`[webhook-poller] reconcilePlanState failed: ${result.error}`);
    return;
  }
  for (const action of result.data) {
    await deliverWebhookEvent("plan_state.enforcement_triggered", {
      namespace: action.namespace,
      action: action.action,
      planState: action.planState,
      at: action.at,
    });
  }
}

/**
 * recomputeAllOverageEstimates() (lib/overage-billing.ts) is the estimate
 * side of usage-based overage billing -- real Prometheus usage x real
 * TIER_RESOURCE_QUOTAS baseline, persisted into the
 * `platform-console-stripe-subscriptions` ConfigMap's `overage.*` keys so
 * /api/billing/overage's GET (and the /billing page's Overage card) never
 * shows a number staler than 10s. Deliberately never calls Stripe itself
 * -- see lib/overage-billing.ts's header comment for why committing a
 * real InvoiceItem is reached only from the owner-gated POST route, not
 * an unattended poll tick.
 */
async function pollOverageEstimates(): Promise<void> {
  const result = await recomputeAllOverageEstimates();
  if (!result.ok) {
    console.error(`[webhook-poller] recomputeAllOverageEstimates failed: ${result.error}`);
  }
}

async function tick(): Promise<void> {
  if (!hasClusterCredentials()) return; // local dev / build -- nothing to poll
  await Promise.all([
    pollBackupCompletions(),
    pollAlertFirings(),
    pollBudgetThresholds(),
    pollCostAnomalies(),
    pollQuotaEnforcement(),
    pollPlanState(),
    pollOverageEstimates(),
  ]);
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
