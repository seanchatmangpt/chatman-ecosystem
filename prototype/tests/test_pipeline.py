"""Real, state-based tests for the full compound.py hop chain, the
jurisdiction registry, and the ConservationVerifier. No unittest.mock,
Mock, MagicMock, patch, or monkeypatch -- only real objects and assertions
on actual return values or raised exceptions.
"""

import pytest

import compound
import jurisdiction
from jurisdiction import JURISDICTION_TABLE, JurisdictionViolation
from verifier import ConservationVerifier, ConservationViolation


def test_full_hop_chain_end_to_end_produces_valid_receipt():
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
    assert all(preserved.values())

    required_keys = ("identity", "authority", "consequence", "replay", "standing")
    assert isinstance(receipt, dict)
    for key in required_keys:
        assert key in receipt
        assert receipt[key]


def test_check_jurisdiction_raises_for_disallowed_pair():
    # ash_r2rml is only permitted to act on "B" per JURISDICTION_TABLE.
    assert "Omega" not in JURISDICTION_TABLE["ash_r2rml"]

    with pytest.raises(JurisdictionViolation):
        jurisdiction.check_jurisdiction("ash_r2rml", "Omega")


def test_check_jurisdiction_does_not_raise_for_allowed_pair():
    assert "B" in JURISDICTION_TABLE["ash_r2rml"]

    assert jurisdiction.check_jurisdiction("ash_r2rml", "B") is True


def test_check_authority_grant_raises_for_invalid_granted_by():
    verifier_instance = ConservationVerifier()
    authority = {"type": "Authority", "sigmaClass": "Handoff", "grantedBy": "Nobody"}

    with pytest.raises(ConservationViolation):
        verifier_instance.check_authority_grant(authority)


def test_check_authority_grant_returns_true_for_grant():
    verifier_instance = ConservationVerifier()
    authority = {"type": "Authority", "sigmaClass": "Handoff", "grantedBy": "Grant"}

    assert verifier_instance.check_authority_grant(authority) is True


def test_check_do_requires_receipt_raises_when_receipt_is_none():
    verifier_instance = ConservationVerifier()
    action = {"type": "Action", "sigmaClass": "Action", "doPrincipal": "alice"}

    with pytest.raises(ConservationViolation):
        verifier_instance.check_do_requires_receipt(action, None)


def test_check_do_requires_receipt_raises_when_receipt_missing_a_key():
    verifier_instance = ConservationVerifier()
    action = {"type": "Action", "sigmaClass": "Action", "doPrincipal": "alice"}
    incomplete_receipt = {
        "type": "Receipt",
        "identity": "alice",
        "authority": "Grant",
        "consequence": "artifact-42",
        "replay": "2026-09-12T00:00:00Z",
        # "standing" key missing entirely.
    }

    with pytest.raises(ConservationViolation):
        verifier_instance.check_do_requires_receipt(action, incomplete_receipt)


def test_check_planner_output_not_authority_raises_for_possibility_claiming_authority():
    verifier_instance = ConservationVerifier()
    candidate = {"type": "Possibility", "sigmaClass": "Possibility", "isAuthority": True}

    with pytest.raises(ConservationViolation):
        verifier_instance.check_planner_output_not_authority(candidate)
