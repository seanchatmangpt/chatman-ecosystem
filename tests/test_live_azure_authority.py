from __future__ import annotations

import copy
import unittest

from scripts.verify_live_azure_authority import AzureAuthorityRefusal, verify


GYMACT_SHA = "ac436398003630907530331a1eca2d71c3fd50dc"


def blocked() -> dict:
    return {
        "schema": "chatman-ecosystem.live-azure-authority/1",
        "standing": "BLOCKED",
        "blocker": "LIVE_AZURE_AUTHORITY",
        "gymact_subject": {
            "repository": "seanchatmangpt/gymact",
            "sha": GYMACT_SHA,
            "provider": "platform-console-ontology",
            "provider_blob_sha": "efd02f211809c8e8aabd75967b443203f1fcf027",
        },
        "authority": None,
    }


def alive() -> dict:
    data = blocked()
    data["standing"] = "ALIVE"
    data["blocker"] = None
    data["authority"] = {
        "authority_class": "DO",
        "authority_ref": "change:CHG-260819-azure",
        "scopes": ["azure.resource-group.deployment.write"],
        "azure_tenant_id": "11111111-1111-4111-8111-111111111111",
        "azure_subscription_id": "22222222-2222-4222-8222-222222222222",
        "azure_principal_object_id": "33333333-3333-4333-8333-333333333333",
        "credential_kind": "federated_oidc",
        "gymact_execution": {
            "repository": "seanchatmangpt/gymact",
            "sha": GYMACT_SHA,
            "executed_sha": GYMACT_SHA,
            "provider": "platform-console-ontology",
            "result": "ADMITTED",
            "receipt": "receipt:gymact-live-azure",
            "verifier": "verifier:gymact-authority",
            "replay": "replay:gymact-live-azure",
        },
        "brce": {
            "exclusive_do_path": True,
            "zero_unreceipted_actuation": True,
            "receipt": "receipt:brce-live-azure",
            "verifier": "verifier:brce-live-azure",
            "replay": "replay:brce-live-azure",
        },
        "live_probe": {
            "scope": "azure.resource-group.deployment.write",
            "executed": True,
            "consequence_class": "DO",
            "receipt": "receipt:azure-live-probe",
            "replay": "replay:azure-live-probe",
        },
    }
    return data


class LiveAzureAuthorityTests(unittest.TestCase):
    def test_blocked_without_authority_is_preserved(self) -> None:
        report = verify(blocked())
        self.assertEqual(report["effective_standing"], "BLOCKED:LIVE_AZURE_AUTHORITY")
        self.assertFalse(report["do_authority"])

    def test_exact_bounded_gymact_brce_live_evidence_can_transition_alive(self) -> None:
        report = verify(alive())
        self.assertEqual(report["effective_standing"], "ALIVE")
        self.assertTrue(report["authority_admitted"])
        self.assertEqual(report["gymact_subject"], GYMACT_SHA)

    def test_gymact_identity_drift_refused(self) -> None:
        data = alive()
        data["authority"]["gymact_execution"]["executed_sha"] = "0" * 40
        with self.assertRaisesRegex(AzureAuthorityRefusal, "REFUSED:GYMACT_EXECUTION_IDENTITY"):
            verify(data)

    def test_ambient_scope_refused(self) -> None:
        data = alive()
        data["authority"]["scopes"] = ["azure.*"]
        with self.assertRaisesRegex(AzureAuthorityRefusal, "REFUSED:AZURE_SCOPE_AMBIENT_OR_UNBOUNDED"):
            verify(data)

    def test_probe_must_execute_inside_admitted_scope(self) -> None:
        data = alive()
        data["authority"]["live_probe"]["executed"] = False
        with self.assertRaisesRegex(AzureAuthorityRefusal, "REFUSED:LIVE_AZURE_DO_NOT_EXECUTED"):
            verify(data)

    def test_brce_must_remain_exclusive_do_path(self) -> None:
        data = alive()
        data["authority"]["brce"]["exclusive_do_path"] = False
        with self.assertRaisesRegex(AzureAuthorityRefusal, "REFUSED:BRCE_NOT_EXCLUSIVE_DO_PATH"):
            verify(data)

    def test_secret_material_is_never_an_admission_artifact(self) -> None:
        data = alive()
        data["authority"]["client_secret"] = "must-not-be-here"
        with self.assertRaisesRegex(AzureAuthorityRefusal, "REFUSED:SECRET_MATERIAL_FORBIDDEN"):
            verify(data)

    def test_capability_is_not_authority(self) -> None:
        data = blocked()
        data["standing"] = "ALIVE"
        data["blocker"] = None
        with self.assertRaises(AzureAuthorityRefusal):
            verify(data)


if __name__ == "__main__":
    unittest.main()
