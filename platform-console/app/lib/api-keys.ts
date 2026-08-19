/**
 * Real hyperscaler-PaaS-style API key self-service (AWS IAM access keys /
 * GCP service account keys / Stripe API keys equivalent) -- the piece that
 * makes this console genuinely programmatically drivable, not just
 * browser-session-drivable. Every real hyperscaler PaaS ships a CLI/SDK
 * path alongside its web console; before this module, every single
 * capability in this app required a browser session cookie (see
 * middleware.ts / lib/session.ts), which is not a real PaaS expectation.
 *
 * Keys are generated cryptographically random (`crypto.randomBytes(32)`,
 * base64url-encoded -- 256 bits of entropy), prefixed `pk_live_` the same
 * way Stripe prefixes its own live secret keys, and stored HASHED
 * (SHA-256, one-way) -- the plaintext key is never stored anywhere past
 * the single response that creates it, and is not recoverable after that.
 * Storage is a real k8s Secret (`platform-console-api-keys`,
 * `platform-console` namespace -- a Secret, not a ConfigMap, precisely
 * because these are key hashes, and this repo already treats that
 * sensitivity class as Secret-worthy even where the value is one-way; see
 * lib/k8s.ts's own Secrets Manager section header). Reuses that exact
 * Secrets CRUD pattern (`getSecretData`/`createOrUpdateSecret`, the same
 * merge-patch-per-key convention `createOrUpdateConfigMap` established
 * for Feature Flags/Org Roles/Webhooks) rather than inventing a new k8s
 * object kind. One Secret data key per API key (`key-<12 hex chars>`),
 * value = one JSON-encoded `ApiKeyRecord`.
 *
 * Role binding reuses the Org RBAC model in lib/authz.ts unchanged: a key
 * is created FOR the creating owner's own identity (never an arbitrary
 * other identity -- minting a key "as" someone else would be identity
 * spoofing, not a feature any real hyperscaler IAM console offers), with
 * a role that must be <= the creator's own current role
 * (`clampRoleToCreator`, `ROLES.indexOf`), defaulting to the creator's own
 * role when omitted -- never escalated. middleware.ts resolves a
 * presented `Authorization: Bearer pk_live_...` header into a real,
 * normal `SessionPayload` (the new `authProvider: "api-key"` variant,
 * lib/session.ts) carrying that fixed `boundRole` claim; lib/authz.ts's
 * `getRoleFor` short-circuits straight to that claim for api-key sessions
 * -- so every existing `requireRole()` gate on every route keeps working
 * completely unchanged. This is purely an alternate authentication method
 * feeding the exact same authorization layer, not a parallel one.
 *
 * Disclosed simplification: no `lastUsedAt` tracking. Recording it would
 * require a real Secret write on every single Bearer-authenticated
 * request, risking concurrent merge-patch races under load for a
 * property no control in this console currently depends on; a real
 * `revoked`/`revokedAt` state (which every proof in the evidence bundle
 * exercises) is tracked instead.
 */
import crypto from "node:crypto";
import { createOrUpdateSecret, getSecretData, type K8sResult } from "@/lib/k8s";
import { ROLES, type Role } from "@/lib/authz";
import { DEFAULT_API_KEY_TIER, isApiKeyTier, type ApiKeyTier } from "@/lib/rate-limit";

export const API_KEYS_NAMESPACE = "platform-console";
export const API_KEYS_SECRET = "platform-console-api-keys";

const KEY_PREFIX = "pk_live_";

export interface ApiKeyRecord {
  id: string;
  prefix: string; // shown in listings -- e.g. "pk_live_AbCd1234..." -- never the full key
  hash: string; // sha256(plaintext), hex -- the only thing this app ever persists
  identifier: string; // bound org-roles identity (roleIdentifierFor-shaped)
  role: Role;
  createdBy: string; // identifier of the owner who created this key
  createdAt: string;
  name: string;
  revoked: boolean;
  revokedAt: string | null;
  // Rate-limit plan tier bound to this key (lib/rate-limit.ts,
  // middleware.ts's per-key token bucket) -- "standard" for every key
  // minted before this field existed (see parseRecord's default below),
  // so a pre-existing key's effective ceiling is unchanged by this
  // addition, not silently widened or narrowed.
  tier: ApiKeyTier;
}

export type ApiKeySummary = Omit<ApiKeyRecord, "hash">;

function toSummary(record: ApiKeyRecord): ApiKeySummary {
  const { hash: _hash, ...summary } = record;
  return summary;
}

function secretDataKeyFor(id: string): string {
  return `key-${id}`;
}

function isRole(value: unknown): value is Role {
  return typeof value === "string" && (ROLES as string[]).includes(value);
}

function parseRecord(raw: string): ApiKeyRecord | null {
  try {
    const parsed = JSON.parse(raw) as Partial<ApiKeyRecord>;
    if (
      typeof parsed.id !== "string" ||
      typeof parsed.prefix !== "string" ||
      typeof parsed.hash !== "string" ||
      typeof parsed.identifier !== "string" ||
      !isRole(parsed.role) ||
      typeof parsed.createdBy !== "string" ||
      typeof parsed.createdAt !== "string" ||
      typeof parsed.revoked !== "boolean"
    ) {
      return null;
    }
    return {
      id: parsed.id,
      prefix: parsed.prefix,
      hash: parsed.hash,
      identifier: parsed.identifier,
      role: parsed.role,
      createdBy: parsed.createdBy,
      createdAt: parsed.createdAt,
      name: typeof parsed.name === "string" ? parsed.name : "",
      revoked: parsed.revoked,
      revokedAt: typeof parsed.revokedAt === "string" ? parsed.revokedAt : null,
      // Backward compatible: a record written before this field existed
      // has no `tier` key at all -- defaults to "standard", the same
      // ceiling every key effectively had (via the flat Envoy filter)
      // before per-tier limits existed.
      tier: isApiKeyTier(parsed.tier) ? parsed.tier : DEFAULT_API_KEY_TIER,
    };
  } catch {
    return null;
  }
}

/** Real cryptographically random key material -- never derived, never predictable. */
function generateKeyMaterial(): { plaintext: string; hash: string; prefix: string } {
  const plaintext = `${KEY_PREFIX}${crypto.randomBytes(32).toString("base64url")}`;
  const hash = crypto.createHash("sha256").update(plaintext, "utf8").digest("hex");
  // Shown in listings so an owner can tell keys apart without the console
  // ever holding the full value again -- same convention real providers
  // use (Stripe shows `sk_live_51H...`, AWS shows the access key ID in
  // full but never the paired secret key past creation).
  const prefix = `${plaintext.slice(0, KEY_PREFIX.length + 8)}...`;
  return { plaintext, hash, prefix };
}

function safeEqualHex(a: string, b: string): boolean {
  const bufA = Buffer.from(a, "hex");
  const bufB = Buffer.from(b, "hex");
  if (bufA.length !== bufB.length) return false;
  return crypto.timingSafeEqual(bufA, bufB);
}

/**
 * Clamps a requested role to at most the creator's own current role -- the
 * "never escalated" invariant. `creatorRole` must be the creator's real,
 * live role (resolved via lib/authz.ts's getRoleFor), never a role the
 * caller merely claims to have.
 */
export function clampRoleToCreator(requested: Role | undefined, creatorRole: Role): Role {
  if (!requested) return creatorRole;
  return ROLES.indexOf(requested) <= ROLES.indexOf(creatorRole) ? requested : creatorRole;
}

export interface CreateApiKeyInput {
  identifier: string;
  creatorRole: Role;
  createdBy: string;
  requestedRole?: Role;
  name?: string;
  // Plan tier this key should be rate-limited under (lib/rate-limit.ts).
  // Unlike `requestedRole`, tier is never clamped against the creator's
  // own role -- a key's tier reflects the *customer's paid plan*, an
  // orthogonal axis from the app-level RBAC role bound to the key, so
  // any owner may mint a key at any tier for their own identity. Defaults
  // to "standard" when omitted or invalid.
  tier?: ApiKeyTier;
}

export async function createApiKey(
  input: CreateApiKeyInput,
): Promise<K8sResult<{ plaintext: string; key: ApiKeySummary }>> {
  const role = clampRoleToCreator(input.requestedRole, input.creatorRole);
  const { plaintext, hash, prefix } = generateKeyMaterial();
  const record: ApiKeyRecord = {
    id: crypto.randomBytes(6).toString("hex"),
    prefix,
    hash,
    identifier: input.identifier,
    role,
    createdBy: input.createdBy,
    createdAt: new Date().toISOString(),
    name: input.name?.trim() || "",
    revoked: false,
    revokedAt: null,
    tier: isApiKeyTier(input.tier) ? input.tier : DEFAULT_API_KEY_TIER,
  };

  const result = await createOrUpdateSecret(API_KEYS_NAMESPACE, API_KEYS_SECRET, {
    [secretDataKeyFor(record.id)]: JSON.stringify(record),
  });
  if (!result.ok) return result;
  return { ok: true, data: { plaintext, key: toSummary(record) } };
}

export async function listApiKeys(): Promise<K8sResult<ApiKeySummary[]>> {
  const result = await getSecretData(API_KEYS_NAMESPACE, API_KEYS_SECRET);
  if (!result.ok) return result;
  const records: ApiKeyRecord[] = [];
  for (const raw of Object.values(result.data ?? {})) {
    const record = parseRecord(raw);
    if (record) records.push(record);
  }
  records.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  return { ok: true, data: records.map(toSummary) };
}

/**
 * Single-key lookup by id -- backs GET /api/orgs/[id]/api-keys/[keyId]/usage
 * (the route needs to confirm the keyId in the URL actually names a real,
 * live key -- returning `data: null` on a real-but-unresolved id, distinct
 * from the `ok: false` transport/Secret-read failure path -- before ever
 * calling lib/audit-db.ts's queryApiKeyUsage). Same read-then-parse shape
 * as revokeApiKey/updateApiKeyTier, just without the write.
 */
export async function getApiKeyById(id: string): Promise<K8sResult<ApiKeySummary | null>> {
  const result = await getSecretData(API_KEYS_NAMESPACE, API_KEYS_SECRET);
  if (!result.ok) return result;
  const raw = result.data?.[secretDataKeyFor(id)];
  const record = raw ? parseRecord(raw) : null;
  return { ok: true, data: record ? toSummary(record) : null };
}

export async function revokeApiKey(id: string): Promise<K8sResult<ApiKeySummary>> {
  const result = await getSecretData(API_KEYS_NAMESPACE, API_KEYS_SECRET);
  if (!result.ok) return result;
  const raw = result.data?.[secretDataKeyFor(id)];
  const record = raw ? parseRecord(raw) : null;
  if (!record) return { ok: false, error: `no api key found with id '${id}'` };

  if (!record.revoked) {
    record.revoked = true;
    record.revokedAt = new Date().toISOString();
    const patched = await createOrUpdateSecret(API_KEYS_NAMESPACE, API_KEYS_SECRET, {
      [secretDataKeyFor(id)]: JSON.stringify(record),
    });
    if (!patched.ok) return patched;
  }
  return { ok: true, data: toSummary(record) };
}

/**
 * Real tier upgrade/downgrade on an EXISTING key -- distinct from
 * `CreateApiKeyInput.tier` (set once at mint time): this is the mutation
 * the "rate-limit tier as a paid add-on" capability needs, called from
 * PUT /api/api-keys/[id]/rate-limit after that route has already gated on
 * `owner` and (for an actual upgrade) attached the real Stripe add-on
 * price via lib/stripe-billing.ts's `attachRateLimitAddonPrice`. Read-
 * modify-write against the same Secret key every other mutation here
 * uses -- no separate storage for the tier field.
 */
export async function updateApiKeyTier(
  id: string,
  tier: ApiKeyTier,
): Promise<K8sResult<ApiKeySummary>> {
  const result = await getSecretData(API_KEYS_NAMESPACE, API_KEYS_SECRET);
  if (!result.ok) return result;
  const raw = result.data?.[secretDataKeyFor(id)];
  const record = raw ? parseRecord(raw) : null;
  if (!record) return { ok: false, error: `no api key found with id '${id}'` };
  if (record.revoked) return { ok: false, error: `api key '${id}' is revoked` };

  if (record.tier !== tier) {
    record.tier = tier;
    const patched = await createOrUpdateSecret(API_KEYS_NAMESPACE, API_KEYS_SECRET, {
      [secretDataKeyFor(id)]: JSON.stringify(record),
    });
    if (!patched.ok) return patched;
  }
  return { ok: true, data: toSummary(record) };
}

export interface ResolvedApiKeyAuth {
  identifier: string;
  role: Role;
  keyId: string;
  tier: ApiKeyTier;
}

/**
 * Resolves a presented Bearer token into the identity+role it authenticates
 * as -- `null` on any of: wrong prefix, no matching hash, or a revoked
 * key. Called from middleware.ts on every API request that arrives with
 * no valid session cookie and an `Authorization: Bearer pk_live_...`
 * header. Hash comparison uses `crypto.timingSafeEqual` (not `===`) so a
 * failed lookup can't leak timing information about how close a guessed
 * key was to a real one.
 */
export async function resolveApiKeyAuth(
  presentedKey: string,
): Promise<ResolvedApiKeyAuth | null> {
  if (!presentedKey.startsWith(KEY_PREFIX)) return null;
  const hash = crypto.createHash("sha256").update(presentedKey, "utf8").digest("hex");

  const result = await getSecretData(API_KEYS_NAMESPACE, API_KEYS_SECRET);
  if (!result.ok || !result.data) return null;

  for (const raw of Object.values(result.data)) {
    const record = parseRecord(raw);
    if (record && safeEqualHex(record.hash, hash)) {
      if (record.revoked) return null;
      return { identifier: record.identifier, role: record.role, keyId: record.id, tier: record.tier };
    }
  }
  return null;
}
