"""Minimal runtime conservation verifier for the Chatman Semantic Coordination Machine.

Enforces calculus invariants over Z = (P, Gamma, Omega, B, tau, J, Authority, Receipts):
SELECT is not CONSTRUCT is not DO, PlannerOutput is not Authority, DO requires a Receipt,
and new Authority requires an explicit Grant, Delegation, or Rule.

Two checks below port real patterns found by cross-repo reconnaissance rather than
inventing new ones (reuse-before-invention discipline):

  - check_receipt_digest: a Receipt's digest must be COMPUTED from its own canonical
    fields, never separately asserted -- the same discipline as praxis-graphlaw's
    Receipt::from_canonical_nquads (crates/praxis-graphlaw/src/chatman/abi.rs:217-260),
    which refuses to build a Receipt from anything but canonical material.
  - check_permit_required_for_actuation: an Action must carry an explicit permit
    reference before it may proceed to DO -- ported from mfw's
    InvocationEnvelope::admit()/Admission (runtime/mfw-rmcp/src/admission.rs:19-48),
    where AuthorizationClass::Actuate is gated on a signed PermitPayload, not merely
    on a "grantedBy" label.
"""

import hashlib


class ConservationViolation(Exception):
    pass


def compute_receipt_digest(receipt):
    """Deterministically hashes a Receipt's own canonical fields (sorted, joined) --
    the digest is never a field someone else asserts; it is always recomputed and
    compared. Mirrors praxis-graphlaw's abi.rs Receipt discipline (hash-from-canonical-
    material, never asserted) ported to Python's stdlib hashlib (sha256) since blake3
    is not part of the Python standard library.
    """
    canonical_keys = ("identity", "authority", "consequence", "replay", "standing")
    material = "|".join(str(receipt.get(key, "")) for key in canonical_keys)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class ConservationVerifier:
    def check_do_requires_receipt(self, action, receipt):
        """Enforces: DO requires a Receipt, and every Receipt carries identity, authority, consequence, replay, standing."""
        if action.get("type") == "Action" and receipt is None:
            raise ConservationViolation("DO requires a Receipt: Action has no receipt")
        if receipt is not None:
            required_keys = ("identity", "authority", "consequence", "replay", "standing")
            missing = [key for key in required_keys if not receipt.get(key)]
            if missing:
                raise ConservationViolation(
                    "Receipt missing required truthy keys: " + ", ".join(missing)
                )
        return True

    def check_authority_grant(self, authority):
        """Enforces: new Authority requires an explicit Grant, Delegation, or Rule."""
        if authority.get("grantedBy") not in ("Grant", "Delegation", "Rule"):
            raise ConservationViolation(
                "Authority has no explicit Grant, Delegation, or Rule: grantedBy=%r"
                % (authority.get("grantedBy"),)
            )
        return True

    def check_planner_output_not_authority(self, candidate):
        """Enforces: PlannerOutput is not Authority (Possibility/State candidates cannot self-declare authority)."""
        if candidate.get("type") in ("Possibility", "State") and candidate.get("isAuthority") is True:
            raise ConservationViolation(
                "PlannerOutput is not Authority: candidate of type %r declares isAuthority=True"
                % (candidate.get("type"),)
            )
        return True

    def check_receipt_digest(self, receipt):
        """Enforces: a Receipt's receiptDigest must equal the recomputed digest of its own canonical fields (never separately asserted)."""
        expected = compute_receipt_digest(receipt)
        actual = receipt.get("receiptDigest")
        if actual != expected:
            raise ConservationViolation(
                "Receipt digest mismatch: receiptDigest=%r does not match recomputed digest %r "
                "of its own canonical fields (a Receipt must be computed, never asserted)"
                % (actual, expected)
            )
        return True

    def check_permit_required_for_actuation(self, action):
        """Enforces: an Action requires an explicit permit reference before DO, not merely a grantedBy label (mfw Admission pattern)."""
        if action.get("type") == "Action" and not action.get("permitRef"):
            raise ConservationViolation(
                "Action has no permitRef: actuation requires an explicit permit, "
                "matching mfw's AuthorizationClass::Actuate gate on a signed PermitPayload"
            )
        return True

    def check_no_self_certification(self, receipt, issuer_component):
        """Enforces: a component cannot certify its own Receipt (issuer, subject, and self-certification cannot all coincide)."""
        if (
            receipt.get("issuedBy") == issuer_component
            and receipt.get("subjectComponent") == issuer_component
            and receipt.get("selfCertified") is True
        ):
            raise ConservationViolation(
                "Self-certification: component %r issued and is the subject of its own self-certified receipt"
                % (issuer_component,)
            )
        return True

    def verify_transition(
        self,
        candidate=None,
        authority=None,
        action=None,
        receipt=None,
        issuer_component=None,
    ):
        """Runs every applicable conservation check for a transition, collecting all violations before raising."""
        violations = []

        if candidate is not None:
            try:
                self.check_planner_output_not_authority(candidate)
            except ConservationViolation as exc:
                violations.append(str(exc))

        if authority is not None:
            try:
                self.check_authority_grant(authority)
            except ConservationViolation as exc:
                violations.append(str(exc))

        if action is not None:
            try:
                self.check_do_requires_receipt(action, receipt)
            except ConservationViolation as exc:
                violations.append(str(exc))
            try:
                self.check_permit_required_for_actuation(action)
            except ConservationViolation as exc:
                violations.append(str(exc))

        if receipt is not None:
            try:
                self.check_receipt_digest(receipt)
            except ConservationViolation as exc:
                violations.append(str(exc))

        if receipt is not None and issuer_component is not None:
            try:
                self.check_no_self_certification(receipt, issuer_component)
            except ConservationViolation as exc:
                violations.append(str(exc))

        if violations:
            raise ConservationViolation("; ".join(violations))

        return True
