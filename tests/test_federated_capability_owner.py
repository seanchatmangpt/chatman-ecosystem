import copy
import importlib.util
import pathlib
import subprocess
import tempfile
import tomllib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_federated_capability_owner",
    ROOT / "scripts" / "verify_federated_capability_owner.py",
)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


def head() -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()


def descriptor(owner_id: str, repository: str, authorities: list[str], capabilities: list[dict], *, simulation_only: bool = False) -> dict:
    return {
        "schema": module.SCHEMA,
        "version": "26.9.1",
        "repository": repository,
        "owner_id": owner_id,
        "control_plane_repository": module.CONTROL_REPOSITORY,
        "control_plane_subject": f"git:{head()}",
        "base_sha": "0" * 40,
        "allowed_authorities": authorities,
        "simulation_only": simulation_only,
        "ambient_do": False,
        "capability": capabilities,
    }


def write_toml(payload: dict, path: pathlib.Path) -> None:
    lines = [
        f'schema = "{payload["schema"]}"',
        f'version = "{payload["version"]}"',
        f'repository = "{payload["repository"]}"',
        f'owner_id = "{payload["owner_id"]}"',
        f'control_plane_repository = "{payload["control_plane_repository"]}"',
        f'control_plane_subject = "{payload["control_plane_subject"]}"',
        f'base_sha = "{payload["base_sha"]}"',
        "allowed_authorities = [" + ", ".join(f'"{x}"' for x in payload["allowed_authorities"]) + "]",
        f'simulation_only = {str(payload["simulation_only"]).lower()}',
        f'ambient_do = {str(payload["ambient_do"]).lower()}',
        "",
    ]
    for item in payload["capability"]:
        lines.extend([
            "[[capability]]",
            f'id = "{item["id"]}"',
            f'relationship = "{item["relationship"]}"',
            f'standing = "{item["standing"]}"',
            f'broker_required = {str(item["broker_required"]).lower()}',
            f'receipt_required = {str(item["receipt_required"]).lower()}',
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


class FederationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = module.load_capabilities(ROOT)
        cls.by_owner = {}
        for item in cls.items:
            cls.by_owner.setdefault(item["owner"], []).append(item)

    def owner_projection(self, owner_id: str) -> list[dict]:
        return [
            {
                "id": item["id"],
                "relationship": "owner",
                "standing": "CANDIDATE",
                "broker_required": item["broker_required"],
                "receipt_required": item["receipt_required"],
            }
            for item in self.by_owner.get(owner_id, [])
        ]

    def admit_payload(self, payload: dict):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "owner.toml"
            write_toml(payload, path)
            return module.admit(payload, ROOT, path, payload["repository"])

    def test_autofde_owner_projects_do_without_ambient_do(self):
        payload = descriptor(
            "repository:autofde",
            "seanchatmangpt/autofde",
            ["persist_control_plane", "modify_external_object"],
            self.owner_projection("repository:autofde"),
        )
        result = self.admit_payload(payload)
        self.assertFalse(result["ambient_do"])
        self.assertFalse(result["capability_standing_promoted"])
        self.assertEqual(result["owned_capabilities"], 2)

    def test_owner_coverage_is_fail_closed(self):
        payload = descriptor(
            "repository:autofde-lab",
            "seanchatmangpt/autofde-lab",
            ["classify"],
            self.owner_projection("repository:autofde-lab")[:-1],
        )
        with self.assertRaisesRegex(module.FederationError, "REFUSED:OWNER_CAPABILITY_COVERAGE"):
            self.admit_payload(payload)

    def test_ambient_do_is_refused_even_for_broker_owner(self):
        payload = descriptor(
            "repository:autofde",
            "seanchatmangpt/autofde",
            ["persist_control_plane", "modify_external_object"],
            self.owner_projection("repository:autofde"),
        )
        payload["ambient_do"] = True
        with self.assertRaisesRegex(module.FederationError, "REFUSED:AMBIENT_DO"):
            self.admit_payload(payload)

    def test_source_participation_does_not_gain_broker_or_receipt(self):
        payload = descriptor(
            "repository:rrgym",
            "seanchatmangpt/rrgym",
            ["observe", "classify"],
            [{
                "id": "capability:execute-bounded-domain-gym",
                "relationship": "source",
                "standing": "CANDIDATE",
                "broker_required": False,
                "receipt_required": False,
            }],
            simulation_only=True,
        )
        result = self.admit_payload(payload)
        self.assertEqual(result["owned_capabilities"], 0)
        self.assertEqual(result["source_participations"], 1)

    def test_simulation_authority_escape_is_refused(self):
        payload = descriptor(
            "repository:rrgym",
            "seanchatmangpt/rrgym",
            ["observe", "modify_external_object"],
            [{
                "id": "capability:execute-bounded-domain-gym",
                "relationship": "source",
                "standing": "CANDIDATE",
                "broker_required": False,
                "receipt_required": False,
            }],
            simulation_only=True,
        )
        with self.assertRaisesRegex(module.FederationError, "REFUSED:SIMULATION_AUTHORITY_ESCAPE"):
            self.admit_payload(payload)


if __name__ == "__main__":
    unittest.main()
