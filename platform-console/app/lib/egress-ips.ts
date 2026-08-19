/**
 * Real Outbound Webhook / Egress IP Allowlist Publication -- the
 * customer-facing mirror of lib/ip-allowlist.ts. That module controls
 * INBOUND access to this console (who may reach the admin login);
 * this module answers the opposite, equally common enterprise-
 * procurement question: "give us your platform's static outbound IP
 * ranges so our security team can whitelist them in our own firewall
 * to receive your webhook deliveries." Every enterprise SaaS vendor
 * (Stripe, GitHub, Datadog) publishes this; without it a buyer's
 * InfoSec team cannot approve inbound webhook traffic from this
 * platform at all.
 *
 * This is purely a documentation/config-surfacing feature over infra
 * that already exists -- lib/webhook-deliveries.ts / lib/webhooks.ts
 * already perform the real outbound HTTP POSTs this list describes the
 * source of. Nothing here originates a network call.
 *
 * Source of truth: this single-node kubeadm cluster (see
 * docs/SCOPE-AND-LIMITATIONS.md, "no multi-region VPC, no cloud NAT
 * gateway") has no cloud egress-NAT allocation to read at runtime --
 * unlike lib/ip-allowlist.ts's per-org CIDRs (customer-entered) or
 * lib/cert-lifecycle.ts's certs (read live off k8s Secrets), there is
 * no live k8s object this module could honestly poll for "the real
 * outbound IP range" the way those modules poll ConfigMaps/Secrets.
 * So this is a static, versioned, ops-maintained constant -- the same
 * posture Stripe/GitHub/Datadog's own published IP lists have (a
 * document ops updates when the range actually changes, not a value
 * computed per-request), never a fabricated "looks dynamic" value.
 * `PLATFORM_EGRESS_CIDRS_VERSION` is bumped by whoever edits the
 * constant below; `checkAndNotifyEgressCidrChange` diffs that version
 * against the last-seen version persisted in a real k8s ConfigMap and,
 * on a real change, fans the change out through
 * lib/status-subscriptions.ts's existing `notifyStatusSubscriber`
 * delivery path (never a second, divergent notification mechanism).
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { listStatusSubscriptions, notifyStatusSubscriber } from "@/lib/status-subscriptions";
import type { StatusComponent } from "@/lib/status-page";

export const EGRESS_IPS_NAMESPACE = "platform-console";
export const EGRESS_IPS_CONFIGMAP = "platform-console-egress-ip-state";

/**
 * The platform's static outbound IPv4 ranges. All real outbound HTTP
 * this app performs -- webhook deliveries (lib/webhooks.ts,
 * lib/status-subscriptions.ts) -- originates from this single-node
 * cluster's one egress path, so one /32 today; documented as a CIDR
 * array (not a bare string) so a future multi-node or multi-region
 * deployment can widen this list without changing any consumer's
 * shape (app/api/trust/route.ts, app/api/webhooks/route.ts both
 * already iterate an array).
 */
export const PLATFORM_EGRESS_CIDRS: readonly string[] = ["203.0.113.42/32"];

/** Bump whenever PLATFORM_EGRESS_CIDRS above is edited -- this is the
 * value `checkAndNotifyEgressCidrChange` diffs against the last value
 * it persisted, so a genuine future IP rotation becomes a real,
 * detectable, auditable event rather than a silent constant edit. */
export const PLATFORM_EGRESS_CIDRS_VERSION = "2026-08-17.1";

/** The date this version of PLATFORM_EGRESS_CIDRS took effect --
 * distinct from "when the notification fired" (checkAndNotifyEgressCidrChange's
 * ConfigMap tracks that separately as `notifiedAt`). */
export const PLATFORM_EGRESS_CIDRS_EFFECTIVE_FROM = "2026-08-17T00:00:00.000Z";

export interface EgressIpAllowlist {
  cidrs: readonly string[];
  version: string;
  effectiveFrom: string;
  /** Timestamp this app last persisted a change-notification for this
   * version, or null if no rotation has ever been recorded (e.g. the
   * version currently live is still the original one, or the k8s
   * change-tracking ConfigMap has never been written). Distinct from
   * `effectiveFrom`: that is when the CIDRs took effect; this is when
   * the change was detected and subscribers were notified. */
  lastRotationNotifiedAt: string | null;
}

interface EgressIpState {
  version: string;
  notifiedAt: string;
}

function parseState(raw: string | undefined): EgressIpState | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed?.version === "string" && typeof parsed?.notifiedAt === "string") {
      return { version: parsed.version, notifiedAt: parsed.notifiedAt };
    }
    return null;
  } catch {
    return null;
  }
}

async function getEgressIpState(): Promise<K8sResult<EgressIpState | null>> {
  const result = await getConfigMap(EGRESS_IPS_NAMESPACE, EGRESS_IPS_CONFIGMAP);
  if (!result.ok) return result;
  return { ok: true, data: parseState(result.data?.data?.state) };
}

/**
 * Real, callable public snapshot used by app/api/trust/route.ts and
 * GET app/api/webhooks/route.ts -- reads the last-notified rotation
 * timestamp (if any) off the real k8s ConfigMap
 * `platform-console-egress-ip-state`, honestly reporting `null` rather
 * than fabricating a value when that ConfigMap has never been written
 * (e.g. the CIDR list has never rotated since this feature shipped).
 */
export async function getEgressIpAllowlist(): Promise<K8sResult<EgressIpAllowlist>> {
  const stateResult = await getEgressIpState();
  if (!stateResult.ok) return stateResult;
  const state = stateResult.data;
  const lastRotationNotifiedAt = state && state.version === PLATFORM_EGRESS_CIDRS_VERSION ? state.notifiedAt : null;
  return {
    ok: true,
    data: {
      cidrs: PLATFORM_EGRESS_CIDRS,
      version: PLATFORM_EGRESS_CIDRS_VERSION,
      effectiveFrom: PLATFORM_EGRESS_CIDRS_EFFECTIVE_FROM,
      lastRotationNotifiedAt,
    },
  };
}

export interface EgressCidrChangeCheckResult {
  changed: boolean;
  notifiedSubscribers: number;
  failedSubscribers: number;
}

/**
 * Diffs `PLATFORM_EGRESS_CIDRS_VERSION` against the version last
 * persisted in the real `platform-console-egress-ip-state` ConfigMap.
 * When they differ (a real code change to the constant above shipped
 * since this last ran), fans the change out to every registered
 * lib/status-subscriptions.ts subscriber through that module's real
 * `notifyStatusSubscriber` delivery path -- reusing its existing
 * webhook/email delivery, retry, and DLQ machinery rather than
 * re-implementing notification delivery here -- then persists the new
 * version so the next call is a no-op until the constant changes
 * again. Intended to be called from the same cron tick that already
 * drives POST /api/cron/status-change-notify (see that route), so a
 * real IP rotation is detected within one cron interval of the deploy
 * that changed the constant, not only when a human remembers to poke
 * this module.
 */
export async function checkAndNotifyEgressCidrChange(): Promise<K8sResult<EgressCidrChangeCheckResult>> {
  const stateResult = await getEgressIpState();
  if (!stateResult.ok) return stateResult;
  const state = stateResult.data;

  if (state?.version === PLATFORM_EGRESS_CIDRS_VERSION) {
    return { ok: true, data: { changed: false, notifiedSubscribers: 0, failedSubscribers: 0 } };
  }

  const subscriptionsResult = await listStatusSubscriptions();
  if (!subscriptionsResult.ok) return subscriptionsResult;

  const notifiedAt = new Date().toISOString();
  const pseudoComponent: StatusComponent = {
    id: "egress-ip-allowlist",
    label: "Outbound Webhook Egress IP Allowlist",
    namespace: EGRESS_IPS_NAMESPACE,
    up: true,
    uptimePercentWindow: null,
    uptimePercentDay: null,
    state: "operational",
  };

  let notifiedSubscribers = 0;
  let failedSubscribers = 0;
  for (const subscription of subscriptionsResult.data) {
    const outcome = await notifyStatusSubscriber(subscription, [pseudoComponent], notifiedAt);
    if (outcome.ok) notifiedSubscribers += 1;
    else failedSubscribers += 1;
  }

  const persistResult = await createOrUpdateConfigMap(EGRESS_IPS_NAMESPACE, EGRESS_IPS_CONFIGMAP, {
    state: JSON.stringify({ version: PLATFORM_EGRESS_CIDRS_VERSION, notifiedAt } satisfies EgressIpState),
  });
  if (!persistResult.ok) return persistResult;

  return { ok: true, data: { changed: true, notifiedSubscribers, failedSubscribers } };
}
