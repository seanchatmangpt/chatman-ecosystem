import copy
import unittest

from scripts.verify_spg_prior_art import (
    SpgRefusal,
    load_graph,
    load_prior_art,
    semantic_diff,
    validate_graph,
    validate_prior_art_catalog,
)


class PriorArtCourtTest(unittest.TestCase):
    def setUp(self):
        self.known = validate_prior_art_catalog(load_prior_art())

    def test_required_public_formalisms_are_routable(self):
        required = {
            "prior:owl2",
            "prior:shacl",
            "prior:hddl",
            "prior:fond",
            "prior:tla-plus",
            "prior:ocel2",
            "prior:lean4",
        }
        self.assertTrue(required.issubset(self.known))

    def test_unknown_prior_art_is_refused(self):
        graph = load_graph()
        graph["prior_art"][0]["searched"] = ["prior:not-real"]
        graph["prior_art"][0]["selected"] = ["prior:not-real"]
        with self.assertRaisesRegex(SpgRefusal, "UNKNOWN_PRIOR_ART"):
            validate_graph(graph, self.known)

    def test_novel_gap_requires_discharged_search(self):
        graph = load_graph()
        claim = graph["prior_art"][0]
        claim["disposition"] = "NOVEL_GAP"
        claim["selected"] = []
        with self.assertRaisesRegex(
            SpgRefusal, "NOVELTY_WITHOUT_PRIOR_ART_FAILURES"
        ):
            validate_graph(graph, self.known)


class SpgCourtTest(unittest.TestCase):
    def setUp(self):
        self.known = validate_prior_art_catalog(load_prior_art())

    def test_first_sa2a_brce_court_is_structurally_admitted(self):
        result = validate_graph(load_graph(), self.known)
        self.assertEqual(result["state"], "ADMITTED_STRUCTURE")
        self.assertEqual(result["standing"], "NONE")
        self.assertEqual(result["consequential_edges"], 1)
        self.assertEqual(
            set(result["projection_families"]),
            {"hddl", "tla_plus", "ocel2", "sa2a", "brce"},
        )

    def test_consequence_without_authority_is_refused(self):
        graph = load_graph()
        next(edge for edge in graph["edges"] if edge["id"] == "e4")[
            "authority_required"
        ] = "NONE"
        with self.assertRaisesRegex(SpgRefusal, "CONSEQUENCE_WITHOUT_AUTHORITY"):
            validate_graph(graph, self.known)

    def test_consequence_without_receipt_is_refused(self):
        graph = load_graph()
        next(edge for edge in graph["edges"] if edge["id"] == "e4")[
            "receipt_required"
        ] = False
        with self.assertRaisesRegex(SpgRefusal, "CONSEQUENCE_WITHOUT_RECEIPT"):
            validate_graph(graph, self.known)

    def test_projection_cannot_reference_unknown_node(self):
        graph = load_graph()
        graph["projections"]["tla_plus"]["not-a-node"] = "Oops"
        with self.assertRaisesRegex(SpgRefusal, "SPG_PROJECTION_DANGLING"):
            validate_graph(graph, self.known)

    def test_semantic_diff_surfaces_authority_change(self):
        old = load_graph()
        new = copy.deepcopy(old)
        next(edge for edge in new["edges"] if edge["id"] == "e4")[
            "authority_required"
        ] = "OTHER_GRANT"
        delta = semantic_diff(old, new)
        edge = next(item for item in delta["changed_edges"] if item["id"] == "e4")
        self.assertIn("authority_required", edge["changes"])


if __name__ == "__main__":
    unittest.main()
