from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import nexus  # noqa: E402


def _nexus(*names: str, private: int = 0) -> dict:
    members = [{"full_name": name, "visibility": "public", "fork": False, "pushed_at": "2026-09-24T00:00:00Z"} for name in names]
    return {
        "nexus": {"schema": nexus.SCHEMA, "hub": "acme/hub", "owners": ["acme"], "authority": "OBSERVE_ONLY"},
        "observation": {
            "observed_at": "2026-09-24",
            "source": "fixture",
            "total": len(members) + private,
            "public": len(members),
            "private": private,
            "forks": 0,
            "public_names_sha256": nexus.names_digest(names),
        },
        "constellation": [{"id": "core", "title": "Core", "match": ["^hub$"]}, {"id": "other", "title": "Other", "match": [".*"]}],
        "member": members,
    }


def _codes(findings) -> set[str]:
    return {finding.code for finding in findings if finding.blocking}


class NexusPositiveTests(unittest.TestCase):
    def test_canonical_nexus_is_admitted_against_every_registry(self) -> None:
        index = nexus.load_toml(ROOT / nexus.NEXUS)
        findings = nexus.verify(index, nexus.collect_registries(ROOT))
        self.assertEqual(_codes(findings), set(), [f.as_dict() for f in findings if f.blocking])

    def test_canonical_projection_is_current(self) -> None:
        self.assertEqual(nexus.main(["--root", str(ROOT), "render", "--check"]), 0)

    def test_hub_indexes_itself_and_every_catalog_repository_is_joined(self) -> None:
        index = nexus.load_toml(ROOT / nexus.NEXUS)
        names = {member["full_name"] for member in index["member"]}
        self.assertIn(index["nexus"]["hub"], names)
        registries = nexus.collect_registries(ROOT)
        catalog = {c for c, sources in registries.references.items() if "catalog" in sources}
        indexed_or_excluded = {n.lower() for n in names} | {e["full_name"].lower() for e in index.get("exclusion", [])}
        owners = {o.lower() for o in index["nexus"]["owners"]}
        self.assertTrue({c for c in catalog if c.split("/")[0] in owners} <= indexed_or_excluded)

    def test_fixture_admitted_and_refresh_round_trips(self) -> None:
        index = _nexus("acme/hub", "acme/tool")
        self.assertEqual(_codes(nexus.verify(index, nexus.Registries())), set())
        inventory = nexus.admit_inventory(
            [
                {"full_name": "acme/hub", "visibility": "public", "fork": False, "pushed_at": "t"},
                {"full_name": "acme/new", "visibility": "public", "fork": True, "pushed_at": "t"},
                {"full_name": "acme/secret", "visibility": "private", "fork": False, "pushed_at": "t"},
                {"full_name": "other/foreign", "visibility": "public", "fork": False, "pushed_at": "t"},
            ],
            ["acme"],
        )
        refreshed = nexus.refresh(index, inventory, "2026-09-25", "fixture")
        self.assertEqual([m["full_name"] for m in refreshed["member"]], ["acme/hub", "acme/new"])
        self.assertEqual(refreshed["observation"]["private"], 1)
        self.assertNotIn("acme/secret", nexus.dump_nexus(refreshed))
        reparsed = nexus.tomllib.loads(nexus.dump_nexus(refreshed))
        self.assertEqual(_codes(nexus.verify(reparsed, nexus.Registries(), inventory)), set())


class NexusRefusalTests(unittest.TestCase):
    def assertRefused(self, index: dict, code: str, registries: nexus.Registries | None = None) -> None:
        self.assertIn(code, _codes(nexus.verify(index, registries or nexus.Registries())))

    def test_private_name_is_never_published(self) -> None:
        index = _nexus("acme/hub")
        index["member"][0]["visibility"] = "private"
        self.assertRefused(index, "NEXUS_PRIVATE_NAME_PUBLISHED")

    def test_nexus_cannot_assign_standing(self) -> None:
        index = _nexus("acme/hub")
        index["member"][0]["standing"] = "ALIVE"
        self.assertRefused(index, "NEXUS_STANDING_ASSIGNED")

    def test_authority_escalation_is_refused(self) -> None:
        index = _nexus("acme/hub")
        index["nexus"]["authority"] = "DO"
        self.assertRefused(index, "NEXUS_AUTHORITY_ESCALATION")

    def test_duplicate_member_is_refused(self) -> None:
        index = _nexus("acme/hub")
        index["member"].append(copy.deepcopy(index["member"][0]))
        self.assertRefused(index, "NEXUS_DUPLICATE_MEMBER")

    def test_membership_tamper_breaks_digest(self) -> None:
        index = _nexus("acme/hub", "acme/tool")
        index["member"][1]["full_name"] = "acme/tool2"
        self.assertRefused(index, "NEXUS_MEMBERSHIP_DIGEST_MISMATCH")

    def test_count_mismatch_is_refused(self) -> None:
        index = _nexus("acme/hub")
        index["observation"]["public"] = 2
        self.assertRefused(index, "NEXUS_PUBLIC_COUNT_MISMATCH")

    def test_foreign_member_is_refused(self) -> None:
        index = _nexus("acme/hub", "evil/hub")
        self.assertRefused(index, "NEXUS_FOREIGN_MEMBER")

    def test_unclassified_member_is_refused(self) -> None:
        index = _nexus("acme/hub", "acme/tool")
        index["constellation"] = index["constellation"][:1]
        self.assertRefused(index, "NEXUS_UNCLASSIFIED")

    def test_orphan_registry_reference_is_refused_until_excluded(self) -> None:
        index = _nexus("acme/hub")
        registries = nexus.Registries()
        registries.add("acme/ghost", "catalog")
        self.assertRefused(index, "NEXUS_ORPHAN_REFERENCE", registries)
        index["exclusion"] = [{"full_name": "acme/ghost", "reason": "renamed"}]
        self.assertEqual(_codes(nexus.verify(index, registries)), set())
        index["exclusion"] = [{"full_name": "acme/ghost", "reason": ""}]
        self.assertRefused(index, "NEXUS_EXCLUSION_UNREASONED", registries)

    def test_drift_against_live_inventory_is_never_silent(self) -> None:
        index = _nexus("acme/hub", "acme/gone")
        inventory = nexus.admit_inventory(
            [
                {"full_name": "acme/hub", "visibility": "public", "fork": True, "pushed_at": "t"},
                {"full_name": "acme/new", "visibility": "public", "fork": False, "pushed_at": "t"},
            ],
            ["acme"],
        )
        codes = _codes(nexus.drift(index, inventory))
        self.assertEqual(codes, {"NEXUS_DRIFT_UNINDEXED", "NEXUS_DRIFT_VANISHED", "NEXUS_DRIFT_FORK_FLAG"})

    def test_malformed_inventory_is_refused(self) -> None:
        cases = [
            ([], "INVENTORY_EMPTY_OR_NOT_A_LIST"),
            ([{"full_name": "acme/x"}], "INVENTORY_ROW_MALFORMED"),
            ([{"full_name": "not a coordinate", "visibility": "public", "fork": False, "pushed_at": "t"}], "INVENTORY_COORDINATE_INVALID"),
            ([{"full_name": "acme/x", "visibility": "internal", "fork": False, "pushed_at": "t"}], "INVENTORY_VISIBILITY_INVALID"),
            ([{"full_name": "acme/x", "visibility": "public", "fork": "no", "pushed_at": "t"}], "INVENTORY_FORK_NOT_BOOLEAN"),
            ([{"full_name": "acme/x", "visibility": "public", "fork": False, "pushed_at": "t"}] * 2, "INVENTORY_DUPLICATE"),
        ]
        for rows, code in cases:
            with self.subTest(code=code), self.assertRaisesRegex(nexus.NexusRefusal, code):
                nexus.admit_inventory(rows, ["acme"])


if __name__ == "__main__":
    unittest.main()
