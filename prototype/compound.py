"""Canonical semantic compound for the Chatman Semantic Coordination Machine.

A role-relative receipt/continuation artifact belonging to a Principal, projected
through the full lawful chain:

    Ontology -> HDDL/FOND -> Ash -> A2A -> DO boundary -> OCEL/Receipt

Vocabulary reused verbatim from the 20 Sigma classes at
/Users/sac/chatman-ecosystem/packs/scm-sigma-pack/ontology.ttl: Identity,
Principal, Role, Topology, Relation, State, Possibility, Observation,
Projection, Time, Objective, Authority, Grant, Delegation, Handoff,
Continuation, Action, Consequence, Receipt, Standing.

Each hop is a pure function taking the previous hop's output dict and
returning a new dict. SELECT is not CONSTRUCT is not DO: canonical_compound
and project_to_hdld are SELECT/CONSTRUCT-shaped and carry no Authority.
project_to_a2a is the first hop where Authority is acquired, and it must
carry an explicit grantedBy (Grant, Delegation, or Rule) or
ConservationVerifier.check_authority_grant will reject it downstream.
project_to_do_boundary and project_to_receipt are the DO boundary: DO
requires a Receipt, enforced here by ConservationVerifier.
"""

import composition
import jurisdiction
from verifier import ConservationVerifier, ConservationViolation, compute_receipt_digest

__all__ = [
    "canonical_compound",
    "project_to_hdld",
    "project_to_ash",
    "project_to_a2a",
    "project_to_do_boundary",
    "project_to_receipt",
    "check_preserved_properties",
]


def canonical_compound(principal_id, role, artifact_id, ts):
    """SELECT-shaped: the canonical Continuation element, no Authority.

    principal_id: Principal identity this compound belongs to.
    role: Role the compound is relative to.
    artifact_id: identity of the artifact this Continuation continues.
    ts: Time coordinate.
    """
    return {
        "type": "Element",
        "sigmaClass": "Continuation",
        "principal": principal_id,
        "role": role,
        "artifactId": artifact_id,
        "timestamp": ts,
    }


def project_to_hdld(canonical):
    """CONSTRUCT-shaped: project the canonical Continuation into an HDDL/FOND
    Possibility. A Possibility must never carry Authority itself
    (PlannerOutput is not Authority), so isAuthority is always False here.
    """
    return {
        "type": "Possibility",
        "sigmaClass": "Possibility",
        "planPrincipal": canonical["principal"],
        "planRole": canonical["role"],
        "planArtifact": canonical["artifactId"],
        "planTime": canonical["timestamp"],
        "isAuthority": False,
    }


def project_to_ash(hdld):
    """CONSTRUCT-shaped: project the HDDL Possibility into an Ash State via
    composition.project, merging in the ash-specific fields on top of the
    Projection wrapper produced by composition.py.
    """
    projection = composition.project(hdld, hdld["planRole"])
    projection.update(
        {
            "sigmaClass": "State",
            "ashPrincipal": hdld["planPrincipal"],
            "ashArtifact": hdld["planArtifact"],
            "ashTime": hdld["planTime"],
        }
    )
    return projection


def project_to_a2a(ash, granted_by, permit_ref):
    """First hop where Authority is acquired: an A2A Handoff.

    Enforces the jurisdictional boundary (ash_a2a is only permitted to act
    on Z-coordinate "P") before constructing the Handoff. granted_by must be
    one of "Grant", "Delegation", "Rule" for the resulting Authority to
    survive ConservationVerifier.check_authority_grant downstream.

    permit_ref: an explicit permit identifier this Authority is issued
    under, ported from mfw's Admission/InvocationEnvelope pattern
    (runtime/mfw-rmcp/src/admission.rs:19-48), where actuation is gated on a
    signed PermitPayload rather than a bare grantedBy label alone. Must be
    truthy for the resulting Action to survive
    ConservationVerifier.check_permit_required_for_actuation downstream.
    """
    jurisdiction.check_jurisdiction("ash_a2a", "P")
    return {
        "type": "Authority",
        "sigmaClass": "Handoff",
        "a2aPrincipal": ash["ashPrincipal"],
        "a2aArtifact": ash["ashArtifact"],
        "a2aTime": ash["ashTime"],
        "grantedBy": granted_by,
        "permitRef": permit_ref,
    }


def project_to_do_boundary(a2a, verifier):
    """The DO boundary: an Action. Verifies the incoming Authority actually
    carries an explicit Grant/Delegation/Rule, that the a2a candidate does
    not self-declare as Authority in violation of PlannerOutput-is-not-
    Authority, and that an explicit permitRef is present (mfw Admission
    pattern) before constructing the Action.
    """
    verifier.check_authority_grant(a2a)
    verifier.check_planner_output_not_authority(a2a)
    action = {
        "type": "Action",
        "sigmaClass": "Action",
        "doPrincipal": a2a["a2aPrincipal"],
        "doArtifact": a2a["a2aArtifact"],
        "doTime": a2a["a2aTime"],
        "permitRef": a2a.get("permitRef"),
    }
    verifier.check_permit_required_for_actuation(action)
    return action


def project_to_receipt(action, verifier, predecessor_receipt_hashes=None):
    """Terminal hop: an OCEL/Receipt covering the DO Action. DO requires a
    Receipt, enforced here, and the Receipt is checked against
    no-self-certification and against digest recomputation before being
    returned.

    receiptDigest is COMPUTED from the receipt's own canonical fields, never
    separately asserted -- ported from praxis-graphlaw's
    Receipt::from_canonical_nquads discipline
    (crates/praxis-graphlaw/src/chatman/abi.rs:217-260).

    predecessorReceiptHashes chains this receipt to whatever receipts
    preceded it, ported from mfw's MeaningReceipt.authorization_receipts /
    predecessor_receipt_hashes pattern
    (mfw-meaning/src/receipt.rs:109-128; runtime/mfw-rmcp/src/admission.rs:34-48).
    """
    receipt = {
        "type": "Receipt",
        "sigmaClass": "Receipt",
        "identity": action["doPrincipal"],
        "authority": "Grant",
        "consequence": action["doArtifact"],
        "replay": action["doTime"],
        "standing": str(action["doPrincipal"]) + ":" + str(action["doArtifact"]),
        "issuedBy": "chatman-ecosystem",
        "subjectComponent": "chatman-ecosystem",
        "selfCertified": False,
        "predecessorReceiptHashes": list(predecessor_receipt_hashes or []),
    }
    receipt["receiptDigest"] = compute_receipt_digest(receipt)
    verifier.check_do_requires_receipt(action, receipt)
    verifier.check_no_self_certification(receipt, "chatman-ecosystem")
    verifier.check_receipt_digest(receipt)
    return receipt


def check_preserved_properties(canonical, hop_outputs):
    """Checks whether principal, artifactId, timestamp, and role survive
    (under their renamed key at each hop) from canonical all the way to the
    Receipt.

    hop_outputs holds the four downstream hop outputs plus the receipt,
    keyed "hdld", "ash", "a2a", "action", "receipt".

    Decision on role: role is only ever carried explicitly as a named field
    through project_to_hdld (planRole) and project_to_ash (it is passed into
    composition.project(hdld, hdld["planRole"]) and comes back only inside
    the Projection wrapper's "role" key, not as a renamed ash-specific
    field). From project_to_a2a onward there is no ash/a2a/do/receipt field
    that carries role at all -- it is absorbed into the Projection wrapper
    and not re-projected further down the chain. So role is checked for
    survival only up through the ash hop; it is not expected, and is not
    checked, past that point.
    """
    hdld = hop_outputs["hdld"]
    ash = hop_outputs["ash"]
    a2a = hop_outputs["a2a"]
    action = hop_outputs["action"]
    receipt = hop_outputs["receipt"]

    principal_ok = (
        hdld["planPrincipal"] == canonical["principal"]
        and ash["ashPrincipal"] == canonical["principal"]
        and a2a["a2aPrincipal"] == canonical["principal"]
        and action["doPrincipal"] == canonical["principal"]
        and receipt["identity"] == canonical["principal"]
    )

    artifact_ok = (
        hdld["planArtifact"] == canonical["artifactId"]
        and ash["ashArtifact"] == canonical["artifactId"]
        and a2a["a2aArtifact"] == canonical["artifactId"]
        and action["doArtifact"] == canonical["artifactId"]
        and receipt["consequence"] == canonical["artifactId"]
    )

    timestamp_ok = (
        hdld["planTime"] == canonical["timestamp"]
        and ash["ashTime"] == canonical["timestamp"]
        and a2a["a2aTime"] == canonical["timestamp"]
        and action["doTime"] == canonical["timestamp"]
        and receipt["replay"] == canonical["timestamp"]
    )

    # Role survives only through the ash hop (see docstring decision above).
    role_ok = (
        hdld["planRole"] == canonical["role"]
        and ash["role"] == canonical["role"]
    )

    return {
        "principal": principal_ok,
        "artifactId": artifact_ok,
        "timestamp": timestamp_ok,
        "role": role_ok,
    }
