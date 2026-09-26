from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from scripts.release_train.hilt_court import (
    ActionCandidate,
    ActorContract,
    ActorKind,
    AgencyLease,
    AgencyLevel,
    ArtifactStanding,
    ArtifactState,
    ContextPermission,
    HiltCase,
    HumanReservation,
    InteractionMode,
    Operation,
    RelationContract,
    Standing,
    SubjectBinding,
    evaluate,
    run,
)

SUBJECTS = (
    SubjectBinding("seanchatmangpt/ash_a2a", "a" * 40),
    SubjectBinding("seanchatmangpt/ash_atlassian", "b" * 40),
)


def healthy_case(
    *,
    operation: Operation = Operation.READ,
    requested_agency: AgencyLevel = AgencyLevel.OBSERVE,
    interaction_mode: InteractionMode = InteractionMode.REACTIVE,
    capability: str = "artifact-inspection",
    artifact_id: str | None = "design-current",
    relation_id: str | None = None,
    surface: str | None = "engineering",
) -> HiltCase:
    return HiltCase(
        case_id="HILT-001",
        semantic_subject_id="urn:chatman:hilt:test",
        subjects=SUBJECTS,
        actor=ActorContract(
            actor_id="agent:sa2a:worker",
            actor_kind=ActorKind.NON_HUMAN,
            accountability_principal="human:owner",
        ),
        artifacts=(
            ArtifactStanding(
                "design-current",
                ArtifactState.CURRENT,
                "sjira:artifact-standing:42",
            ),
            ArtifactStanding(
                "design-old",
                ArtifactState.SUPERSEDED,
                "sjira:artifact-standing:41",
            ),
            ArtifactStanding(
                "design-unknown",
                ArtifactState.UNKNOWN,
                "sjira:artifact-standing:unknown",
            ),
        ),
        agency_leases=(
            AgencyLease(
                capability,
                "engineering",
                AgencyLevel.BOUNDED_DELEGATED_DO,
                "gall:HILT-lease-001",
            ),
            AgencyLease(
                "debugging",
                "engineering",
                AgencyLevel.BOUNDED_DELEGATED_DO,
                "gall:HILT-debug-001",
            ),
        ),
        permissions=(
            ContextPermission(
                context="engineering",
                operations=(
                    Operation.READ,
                    Operation.SELECT,
                    Operation.CONSTRUCT,
                    Operation.DISCLOSE,
                    Operation.NOTIFY,
                    Operation.RESPOND,
                    Operation.ASSIGN,
                    Operation.SCHEDULE,
                    Operation.CLAIM_RESPONSIBILITY,
                    Operation.EXECUTE,
                ),
                read_artifacts=(
                    "design-current",
                    "design-old",
                    "design-unknown",
                ),
                disclose_artifacts=("design-current",),
                surfaces=("engineering", "incident"),
            ),
        ),
        relations=(
            RelationContract(
                relation_id="team:member:vp",
                relation_kind="MEMBER",
                allowed_operations=(Operation.RESPOND,),
            ),
            RelationContract(
                relation_id="team:oncall:alice",
                relation_kind="RESPONSIBLE",
                allowed_operations=(
                    Operation.NOTIFY,
                    Operation.RESPOND,
                    Operation.ASSIGN,
                ),
            ),
        ),
        human_reservations=(),
        action=ActionCandidate(
            action_id="action-1",
            actor_id="agent:sa2a:worker",
            capability=capability,
            context="engineering",
            operation=operation,
            requested_agency=requested_agency,
            interaction_mode=interaction_mode,
            consequence_class="LOW",
            artifact_id=artifact_id,
            relation_id=relation_id,
            surface=surface,
        ),
    )


class HiltCourtTests(unittest.TestCase):
    def test_current_read_is_alive_with_zero_authority(self) -> None:
        receipt = evaluate(healthy_case())
        self.assertEqual(receipt.standing, Standing.ALIVE)
        self.assertEqual(receipt.authority, "NONE")
        self.assertEqual(receipt.downstream, "NONE")
        self.assertEqual(receipt.admitted_agency, "A0_OBSERVE")

    def test_superseded_artifact_is_refused(self) -> None:
        case = healthy_case()
        receipt = evaluate(
            replace(case, action=replace(case.action, artifact_id="design-old"))
        )
        self.assertEqual(receipt.standing, Standing.REFUSED)
        self.assertIn("REFUSED:SUPERSEDED_ARTIFACT:design-old", receipt.refusals)

    def test_unknown_artifact_standing_blocks(self) -> None:
        case = healthy_case()
        receipt = evaluate(
            replace(case, action=replace(case.action, artifact_id="design-unknown"))
        )
        self.assertEqual(receipt.standing, Standing.BLOCKED)
        self.assertIn(
            "BLOCKED:ARTIFACT_STANDING_UNKNOWN:design-unknown",
            receipt.refusals,
        )

    def test_read_does_not_imply_disclosure(self) -> None:
        case = healthy_case(
            operation=Operation.DISCLOSE,
            requested_agency=AgencyLevel.REQUEST_DO,
            artifact_id="design-old",
        )
        artifacts = tuple(
            replace(x, state=ArtifactState.CURRENT)
            if x.artifact_id == "design-old"
            else x
            for x in case.artifacts
        )
        receipt = evaluate(replace(case, artifacts=artifacts))
        self.assertEqual(receipt.standing, Standing.REFUSED)
        self.assertIn(
            "REFUSED:DISCLOSE_NOT_PERMITTED:design-old",
            receipt.refusals,
        )

    def test_membership_does_not_imply_notification_authority(self) -> None:
        receipt = evaluate(
            healthy_case(
                operation=Operation.NOTIFY,
                requested_agency=AgencyLevel.REQUEST_DO,
                artifact_id=None,
                relation_id="team:member:vp",
            )
        )
        self.assertEqual(receipt.standing, Standing.REFUSED)
        self.assertIn(
            "REFUSED:RELATION_OPERATION_NOT_GRANTED:team:member:vp:NOTIFY",
            receipt.refusals,
        )

    def test_capability_qualification_does_not_leak(self) -> None:
        case = healthy_case(capability="interpersonal-coaching")
        case = replace(
            case,
            agency_leases=tuple(
                x for x in case.agency_leases if x.capability == "debugging"
            ),
        )
        receipt = evaluate(case)
        self.assertEqual(receipt.standing, Standing.BLOCKED)
        self.assertIn(
            "BLOCKED:AGENCY_LEASE_MISSING:interpersonal-coaching:engineering",
            receipt.refusals,
        )

    def test_unearned_agency_escalation_is_refused(self) -> None:
        case = healthy_case(
            operation=Operation.NOTIFY,
            requested_agency=AgencyLevel.BOUNDED_DELEGATED_DO,
            interaction_mode=InteractionMode.PROACTIVE,
            artifact_id=None,
            relation_id="team:oncall:alice",
        )
        leases = tuple(
            replace(x, max_level=AgencyLevel.PROACTIVE_CONSTRUCT)
            if x.capability == "artifact-inspection"
            else x
            for x in case.agency_leases
        )
        receipt = evaluate(replace(case, agency_leases=leases))
        self.assertEqual(receipt.standing, Standing.REFUSED)
        self.assertTrue(
            any(
                x.startswith("REFUSED:AGENCY_EXCEEDS_LEASE:")
                for x in receipt.refusals
            )
        )

    def test_proactive_consequence_requires_a6(self) -> None:
        receipt = evaluate(
            healthy_case(
                operation=Operation.NOTIFY,
                requested_agency=AgencyLevel.PROACTIVE_CONSTRUCT,
                interaction_mode=InteractionMode.PROACTIVE,
                artifact_id=None,
                relation_id="team:oncall:alice",
            )
        )
        self.assertEqual(receipt.standing, Standing.REFUSED)
        self.assertTrue(
            any(
                x.startswith("REFUSED:AGENCY_BELOW_OPERATION_MINIMUM:NOTIFY")
                for x in receipt.refusals
            )
        )

    def test_human_reserved_surface_is_refused(self) -> None:
        case = healthy_case(
            operation=Operation.SCHEDULE,
            requested_agency=AgencyLevel.REQUEST_DO,
            artifact_id=None,
            surface="incident",
        )
        reservation = HumanReservation(
            capability="artifact-inspection",
            context="engineering",
            operation=Operation.SCHEDULE,
            reservation_id="human-only:incident-scheduling",
            surface="incident",
        )
        receipt = evaluate(replace(case, human_reservations=(reservation,)))
        self.assertEqual(receipt.standing, Standing.REFUSED)
        self.assertIn(
            "REFUSED:HUMAN_RESERVED:human-only:incident-scheduling",
            receipt.refusals,
        )

    def test_consequential_admission_still_requires_brce(self) -> None:
        receipt = evaluate(
            healthy_case(
                operation=Operation.NOTIFY,
                requested_agency=AgencyLevel.REQUEST_DO,
                artifact_id=None,
                relation_id="team:oncall:alice",
            )
        )
        self.assertEqual(receipt.standing, Standing.ALIVE)
        self.assertEqual(receipt.authority, "NONE")
        self.assertEqual(receipt.downstream, "BRCE_REQUIRED")

    def test_response_does_not_claim_responsibility(self) -> None:
        receipt = evaluate(
            healthy_case(
                operation=Operation.RESPOND,
                requested_agency=AgencyLevel.REQUEST_DO,
                artifact_id=None,
                relation_id="team:member:vp",
            )
        )
        self.assertEqual(receipt.standing, Standing.ALIVE)
        self.assertFalse(receipt.responsibility_claim)

    def test_explicit_responsibility_claim_requires_relation_grant(self) -> None:
        receipt = evaluate(
            healthy_case(
                operation=Operation.CLAIM_RESPONSIBILITY,
                requested_agency=AgencyLevel.REQUEST_DO,
                artifact_id=None,
                relation_id="team:member:vp",
            )
        )
        self.assertEqual(receipt.standing, Standing.REFUSED)
        self.assertFalse(receipt.responsibility_claim)

    def test_receipt_is_deterministic(self) -> None:
        self.assertEqual(
            evaluate(healthy_case()).receipt_digest,
            evaluate(healthy_case()).receipt_digest,
        )

    def test_json_cli_round_trip(self) -> None:
        payload = {
            "case_id": "HILT-JSON",
            "semantic_subject_id": "urn:chatman:hilt:json",
            "subjects": [
                {
                    "repository": "seanchatmangpt/ash_a2a",
                    "subject_sha": "a" * 40,
                }
            ],
            "actor": {
                "actor_id": "agent:a2a",
                "actor_kind": "NON_HUMAN",
                "accountability_principal": "human:owner",
            },
            "artifacts": [
                {
                    "artifact_id": "spec",
                    "state": "CURRENT",
                    "provenance": "sjira:standing:1",
                }
            ],
            "agency_leases": [
                {
                    "capability": "inspect",
                    "context": "engineering",
                    "max_level": "A0_OBSERVE",
                    "evidence_id": "gall:lease:1",
                }
            ],
            "permissions": [
                {
                    "context": "engineering",
                    "operations": ["READ"],
                    "read_artifacts": ["spec"],
                    "surfaces": ["engineering"],
                }
            ],
            "relations": [],
            "human_reservations": [],
            "action": {
                "action_id": "read-1",
                "actor_id": "agent:a2a",
                "capability": "inspect",
                "context": "engineering",
                "operation": "READ",
                "requested_agency": "A0_OBSERVE",
                "interaction_mode": "REACTIVE",
                "consequence_class": "NONE",
                "artifact_id": "spec",
                "surface": "engineering",
            },
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "case.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            data, code = run(str(path))
        self.assertEqual(code, 0)
        self.assertEqual(data["standing"], "ALIVE")
        self.assertEqual(data["authority"], "NONE")

    def test_unknown_agency_is_typed_refusal(self) -> None:
        payload = {
            "case_id": "HILT-BAD",
            "semantic_subject_id": "urn:chatman:hilt:bad",
            "subjects": [
                {
                    "repository": "seanchatmangpt/ash_a2a",
                    "subject_sha": "a" * 40,
                }
            ],
            "actor": {
                "actor_id": "agent:a2a",
                "actor_kind": "NON_HUMAN",
                "accountability_principal": "human:owner",
            },
            "agency_leases": [
                {
                    "capability": "inspect",
                    "context": "engineering",
                    "max_level": "GLOBAL_TRUST",
                    "evidence_id": "bad",
                }
            ],
            "permissions": [],
            "relations": [],
            "human_reservations": [],
            "action": {
                "action_id": "x",
                "actor_id": "agent:a2a",
                "capability": "inspect",
                "context": "engineering",
                "operation": "READ",
                "requested_agency": "A0_OBSERVE",
                "interaction_mode": "REACTIVE",
                "consequence_class": "NONE",
            },
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "case.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            data, code = run(str(path))
        self.assertEqual(code, 2)
        self.assertIn("unknown agency level GLOBAL_TRUST", data["refusals"][0])


if __name__ == "__main__":
    unittest.main()
