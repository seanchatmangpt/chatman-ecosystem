"""Runnable demonstration of the Chatman Semantic Coordination Machine calculus
Z = (P, Gamma, Omega, B, tau, J, Authority, Receipts) over the full lawful
projection chain:

    canonical_compound -> project_to_hdld -> project_to_ash -> project_to_a2a
    -> project_to_do_boundary -> project_to_receipt

Invariants exercised: SELECT is not CONSTRUCT is not DO, PlannerOutput is not
Authority, DO requires a Receipt, and new Authority requires an explicit
Grant, Delegation, or Rule. Vocabulary reused verbatim from the 20 Sigma
classes committed at /Users/sac/chatman-ecosystem/packs/scm-sigma-pack/ontology.ttl.
"""

import json
import sys

import compound
import jurisdiction
from jurisdiction import JurisdictionViolation
from verifier import ConservationVerifier, ConservationViolation


def main():
    canonical = compound.canonical_compound(
        "principal-alice", "reviewer", "artifact-42", "2026-09-12T00:00:00Z"
    )

    hdld = compound.project_to_hdld(canonical)
    ash = compound.project_to_ash(hdld)
    a2a = compound.project_to_a2a(ash, granted_by="Grant")

    verifier_instance = ConservationVerifier()

    action = compound.project_to_do_boundary(a2a, verifier_instance)
    receipt = compound.project_to_receipt(action, verifier_instance)

    hop_outputs = {
        "hdld": hdld,
        "ash": ash,
        "a2a": a2a,
        "action": action,
        "receipt": receipt,
    }

    preserved = compound.check_preserved_properties(canonical, hop_outputs)
    print(json.dumps(preserved, indent=2))

    print(json.dumps(receipt, indent=2))

    refusal_a_ok = False
    refusal_b_ok = False

    try:
        bad_a2a = dict(a2a)
        bad_a2a["grantedBy"] = "Nobody"
        verifier_instance.check_authority_grant(bad_a2a)
        print("REFUSAL FAILED (no exception)")
    except ConservationViolation as exc:
        print(f"REFUSAL OK: {exc}")
        refusal_a_ok = True

    try:
        jurisdiction.check_jurisdiction("beam4pm", "A")
        print("REFUSAL FAILED (no exception)")
    except JurisdictionViolation as exc:
        print(f"REFUSAL OK: {exc}")
        refusal_b_ok = True

    all_properties_preserved = all(preserved.values())
    both_refusals_ok = refusal_a_ok and refusal_b_ok

    if both_refusals_ok and all_properties_preserved:
        sys.exit(0)

    if not refusal_a_ok:
        print("CHECK FAILED: refusal (a) check_authority_grant did not raise ConservationViolation")
    if not refusal_b_ok:
        print("CHECK FAILED: refusal (b) check_jurisdiction did not raise JurisdictionViolation")
    if not all_properties_preserved:
        failed = [key for key, ok in preserved.items() if not ok]
        print(f"CHECK FAILED: properties not preserved: {failed}")
    sys.exit(1)


if __name__ == "__main__":
    main()
