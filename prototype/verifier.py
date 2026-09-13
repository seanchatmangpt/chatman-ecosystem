"""Minimal runtime conservation verifier for the Chatman Semantic Coordination Machine.

Enforces calculus invariants over Z = (P, Gamma, Omega, B, tau, J, Authority, Receipts):
SELECT is not CONSTRUCT is not DO, PlannerOutput is not Authority, DO requires a Receipt,
and new Authority requires an explicit Grant, Delegation, or Rule.
"""


class ConservationViolation(Exception):
    pass


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

        if receipt is not None and issuer_component is not None:
            try:
                self.check_no_self_certification(receipt, issuer_component)
            except ConservationViolation as exc:
                violations.append(str(exc))

        if violations:
            raise ConservationViolation("; ".join(violations))

        return True
