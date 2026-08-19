import { X509Certificate } from "node:crypto";

/**
 * Real, config-only SAML 2.0 metadata surface -- closes the named gap
 * this repo's evidence bundle documents: lib/oidc-federation.ts and
 * lib/session.ts prove OIDC federation is real and live, but Fortune-5
 * IT/security teams standardize enterprise app onboarding on SAML 2.0
 * (ADFS, Okta SAML apps, Azure AD SAML), not OIDC -- procurement
 * checklists frequently gate on a binary "do you support SAML SSO".
 *
 * This module validates an org admin's submitted IdP metadata (Entity
 * ID, SSO URL, x509 signing certificate) is well-formed -- structurally,
 * offline, via Node's own `crypto.X509Certificate` parser -- and nothing
 * more. It makes NO network call to the IdP (no metadata-URL fetch, no
 * cert-chain validation against a CA) and it is never consumed by
 * lib/session.ts or any auth callback route to authenticate a real
 * session. That is deliberate and fail-closed: this is a pre-flight
 * configuration surface an org admin fills out ahead of a later pass
 * that wires the real SAML assertion-consumer-service (ACS) endpoint,
 * not a working SSO path today. See PutSamlConfigRoute's module doc
 * (app/app/api/orgs/[id]/saml-config/route.ts) and the settings page's
 * status banner for the same disclosure surfaced to the org admin.
 */

export type SamlConfigStatus = "unconfigured" | "configured" | "validated";

export interface SamlConfig {
  entityId: string;
  ssoUrl: string;
  certificatePem: string;
  status: SamlConfigStatus;
  /** ISO 8601 timestamp of the last successful validated save, so the
   * settings UI can show "last updated" without a separate audit-log
   * round-trip for the common case. */
  updatedAt: string;
}

const MAX_ENTITY_ID_LENGTH = 512;
const MAX_CERT_PEM_LENGTH = 16_384;

/**
 * Structural, offline validation of a submitted SAML metadata triple --
 * same fail-closed discipline as lib/orgs.ts's validateBranding: reject
 * and return a real, specific error string (never a fabricated silent
 * default/pass) on anything that doesn't meet the contract, so a bad
 * value can never reach the registry ConfigMap.
 *
 *   - entityId must parse as an absolute URI (SAML Entity IDs are
 *     conventionally URIs -- `urn:...` or `https://...` -- both of which
 *     `new URL()` accepts as long as a scheme is present; this rejects
 *     bare hostnames/free text, same "reject, don't coerce" posture as
 *     validateBranding's logoUrl check).
 *   - ssoUrl must be `https://` -- mirrors validateBranding's logoUrl
 *     rule exactly (rejects `http://`, `data:`, and anything without a
 *     scheme -- an IdP's SSO redirect/POST binding endpoint is never
 *     served over plaintext in a real deployment).
 *   - certificatePem must parse as a real, structurally valid X.509
 *     certificate via Node's built-in `crypto.X509Certificate` -- no
 *     custom PEM/ASN.1 parsing, no network fetch to the IdP to confirm
 *     it, purely a local structural check that the pasted PEM is a real
 *     certificate and not garbage/truncated input.
 *
 * Returns `null` on success (same "no error" convention every validator
 * in this codebase uses), otherwise a specific, user-facing message.
 */
export function validateSamlConfig(input: {
  entityId: string;
  ssoUrl: string;
  certificatePem: string;
}): string | null {
  if (!input.entityId || input.entityId.length > MAX_ENTITY_ID_LENGTH) {
    return `entityId is required and must be at most ${MAX_ENTITY_ID_LENGTH} characters`;
  }
  try {
    // eslint-disable-next-line no-new
    new URL(input.entityId);
  } catch {
    return "entityId must be a valid absolute URI (e.g. https://idp.example.com/saml or urn:example:idp)";
  }

  if (!input.ssoUrl.startsWith("https://")) {
    return "ssoUrl must be an https:// URL";
  }
  try {
    // eslint-disable-next-line no-new
    new URL(input.ssoUrl);
  } catch {
    return "ssoUrl must be a valid https:// URL";
  }

  if (!input.certificatePem || input.certificatePem.length > MAX_CERT_PEM_LENGTH) {
    return `certificatePem is required and must be at most ${MAX_CERT_PEM_LENGTH} characters`;
  }
  if (!/-----BEGIN CERTIFICATE-----/.test(input.certificatePem)) {
    return "certificatePem must be a PEM-encoded X.509 certificate (-----BEGIN CERTIFICATE-----)";
  }
  try {
    // Real, structural X.509 parse via Node's own crypto module -- no
    // network call to the IdP, no CA chain validation, purely "is this
    // actually a well-formed certificate." Throws on malformed/truncated
    // PEM or non-certificate DER content.
    const cert = new X509Certificate(input.certificatePem);
    if (!cert.subject) {
      return "certificatePem parsed but has no subject -- not a usable signing certificate";
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return `certificatePem is not a valid X.509 certificate: ${message}`;
  }

  return null;
}
