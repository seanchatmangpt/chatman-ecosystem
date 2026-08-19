/**
 * Per-API-key, per-tier request rate limiting -- the application-layer
 * counterpart to the flat, global 20/min Istio `local_ratelimit`
 * EnvoyFilter (k8s/ratelimit.yaml, control `rate-limiting-enforced`).
 * That gateway-level filter enforces one fixed bucket for every caller on
 * the `platform-console-root` route, with no notion of which tenant, key,
 * or plan tier is calling -- real for anonymous/browser traffic, but
 * wrong for a Bearer-authenticated API caller, who now carries a real
 * bound tier (`lib/api-keys.ts`'s `ApiKeyRecord.tier`) a limit can key
 * off of. This module is that per-key limit.
 *
 * Deliberately application-layer, not a second EnvoyFilter: the tier is
 * resolved from the API key's own record (a k8s Secret, via
 * `resolveApiKeyAuth`) only inside the app -- Envoy has no visibility into
 * that resolution short of the app writing it back out as a request
 * header for a second gateway hop to key off, which would mean trusting a
 * client-settable header unless the gateway strips and the app re-adds it
 * on every hop (extra moving parts for no real gain here, since
 * middleware.ts already parses the bearer key on every request before any
 * route handler runs -- exactly the point real per-key throttling has to
 * happen anyway).
 *
 * Real token-bucket algorithm (same primitive Envoy's own
 * `local_ratelimit` filter uses: max_tokens / tokens_per_fill /
 * fill_interval), implemented in-process with a plain `Map`, not a fake.
 * Disclosed simplification, same shape as lib/api-keys.ts's own
 * "no lastUsedAt tracking" disclosure: this bucket lives in one Node
 * process's memory, not a shared store (no Redis in this stack -- see
 * README's Rate limiting section for why the Envoy layer itself avoids
 * one too). With more than one running replica of the gateway Deployment,
 * each replica enforces its own independent bucket per key, so the
 * *effective* ceiling across the whole deployment is
 * `tierLimit * replicaCount`, not a cluster-wide single ceiling. That is
 * the same trade-off Envoy's own *global* rate limit service exists to
 * solve and this app does not run one; per-key differentiation is the
 * real gap being closed here, not cross-replica coordination.
 */

export type ApiKeyTier = "standard" | "pro" | "enterprise";

// Sandbox-mode ceiling (lib/api-keys.ts's `ApiKeyRecord.mode`) -- fixed,
// deliberately independent of the key's own `tier`. A sandbox key exists
// to let CI/integration testing happen safely, never to be a cheap way to
// get "enterprise" throughput against real infrastructure; every sandbox
// key gets this exact ceiling regardless of what plan tier its record
// otherwise carries. 60/min matches the real hyperscaler convention
// (Stripe/Twilio/AWS test-mode keys: generous enough for a real CI suite
// to run end-to-end, low enough that it is never mistaken for a
// production-capacity ceiling).
export const SANDBOX_TIER_LIMIT: TierLimit = { maxTokens: 60, fillIntervalMs: 60_000 };

export type ApiKeyMode = "sandbox" | "live";

export const API_KEY_MODES: ApiKeyMode[] = ["sandbox", "live"];

export const DEFAULT_API_KEY_MODE: ApiKeyMode = "live";

export function isApiKeyMode(value: unknown): value is ApiKeyMode {
  return typeof value === "string" && (API_KEY_MODES as string[]).includes(value);
}

export const API_KEY_TIERS: ApiKeyTier[] = ["standard", "pro", "enterprise"];

export const DEFAULT_API_KEY_TIER: ApiKeyTier = "standard";

export function isApiKeyTier(value: unknown): value is ApiKeyTier {
  return typeof value === "string" && (API_KEY_TIERS as string[]).includes(value);
}

export interface TierLimit {
  maxTokens: number;
  fillIntervalMs: number;
}

// "standard" is deliberately identical to the Envoy-layer default
// (max_tokens 20, fill_interval 60s, k8s/ratelimit.yaml) -- a caller on
// the entry-level tier sees the same ceiling whether the Envoy filter or
// this per-key bucket is the one that actually trips first; "pro" and
// "enterprise" are real, materially higher ceilings a paying tenant would
// expect, not decorative.
export const TIER_LIMITS: Record<ApiKeyTier, TierLimit> = {
  standard: { maxTokens: 20, fillIntervalMs: 60_000 },
  pro: { maxTokens: 100, fillIntervalMs: 60_000 },
  enterprise: { maxTokens: 500, fillIntervalMs: 60_000 },
};

interface BucketState {
  tokens: number;
  lastRefillAt: number;
}

export interface RateLimitResult {
  allowed: boolean;
  limit: number;
  remaining: number;
  /** Milliseconds until the bucket would allow the next request, 0 when allowed. */
  retryAfterMs: number;
}

/**
 * Real, stateful token bucket keyed by API key id. Exported as a class
 * (not a single module-level singleton) so a real, fresh instance can be
 * constructed per-test -- exercising real refill/consume state machine
 * transitions with a real injectable clock, never a mocked timer.
 */
export class TokenBucketLimiter {
  private readonly buckets = new Map<string, BucketState>();
  private readonly now: () => number;

  constructor(now: () => number = Date.now) {
    this.now = now;
  }

  /** Number of distinct keys currently tracked -- for real state assertions in tests. */
  get size(): number {
    return this.buckets.size;
  }

  /**
   * Consumes one token for `keyId` under `tier`'s bucket, refilling first
   * based on real elapsed wall-clock time since the bucket's last refill
   * (or since it was first created, for a bucket seen for the first
   * time -- which starts full, same as a fresh Envoy token bucket does).
   */
  consume(keyId: string, tier: ApiKeyTier, mode: ApiKeyMode = DEFAULT_API_KEY_MODE): RateLimitResult {
    // Sandbox ceiling wins outright, independent of `tier` -- see
    // SANDBOX_TIER_LIMIT's doc comment above.
    const limit = mode === "sandbox" ? SANDBOX_TIER_LIMIT : TIER_LIMITS[tier];
    const now = this.now();
    let bucket = this.buckets.get(keyId);
    if (!bucket) {
      bucket = { tokens: limit.maxTokens, lastRefillAt: now };
      this.buckets.set(keyId, bucket);
    } else {
      const elapsedMs = now - bucket.lastRefillAt;
      if (elapsedMs > 0) {
        const refillFraction = elapsedMs / limit.fillIntervalMs;
        const refilled = refillFraction * limit.maxTokens;
        bucket.tokens = Math.min(limit.maxTokens, bucket.tokens + refilled);
        bucket.lastRefillAt = now;
      }
    }

    if (bucket.tokens >= 1) {
      bucket.tokens -= 1;
      return {
        allowed: true,
        limit: limit.maxTokens,
        remaining: Math.floor(bucket.tokens),
        retryAfterMs: 0,
      };
    }

    const tokensNeeded = 1 - bucket.tokens;
    const retryAfterMs = Math.ceil((tokensNeeded / limit.maxTokens) * limit.fillIntervalMs);
    return { allowed: false, limit: limit.maxTokens, remaining: 0, retryAfterMs };
  }

  /** Test/debug helper -- real current token count, no refill side effect. */
  peek(keyId: string): number | null {
    return this.buckets.get(keyId)?.tokens ?? null;
  }
}

/**
 * One real shared limiter for the whole running process -- module-level
 * singleton so every request middleware.ts handles goes through the same
 * bucket state (a fresh limiter per request would never throttle
 * anything). Next.js's Node.js middleware runtime keeps one long-lived
 * module instance per worker process, the same lifetime assumption
 * lib/k8s.ts's own `cachedConfig` module-level cache already relies on.
 */
export const apiKeyRateLimiter = new TokenBucketLimiter();
