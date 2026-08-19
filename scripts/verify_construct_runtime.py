#!/usr/bin/env python3
"""Fail-closed verifier for catalog/construct-runtime.toml.

This verifier admits only the bounded architecture profile encoded in the
catalog. It does not claim that a particular WASM artifact or remote system has
implemented the profile; owning repositories must supply exact-subject runtime
evidence for that standing.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "catalog" / "construct-runtime.toml"


class Refusal(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise Refusal(code)


def verify(path: pathlib.Path) -> dict[str, object]:
    with path.open("rb") as fh:
        data = tomllib.load(fh)

    profile = data["profile"]
    knowledge = data["knowledge"]
    obs = data["observation"]
    manufacture = data["manufacture"]
    interaction = data["interaction"]
    process = data["process"]
    wasm = data["wasm"]
    dispatch = data["dispatch"]
    standing = data["standing"]
    hie = data["hyperdimensional_information_encryption"]
    security = data["security"]
    vision = data["vision_2030"]

    require(profile["equation"] == "A=mu(O*)", "REFUSE_EQUATION_DRIFT")
    require(profile["standing"] == "CANDIDATE", "REFUSE_AMBIENT_ALIVE")

    require(not knowledge["human_has_ambient_authority"], "REFUSE_HUMAN_AMBIENT_AUTHORITY")
    require(not knowledge["llm_has_ambient_authority"], "REFUSE_LLM_AMBIENT_AUTHORITY")
    require(not knowledge["knowledge_equals_standing"], "REFUSE_KNOWLEDGE_AS_STANDING")
    require(knowledge["repeated_cognition_should_be_manufactured"], "REFUSE_REPEATED_COGNITION")
    require(set(knowledge["decomposition_leaf_classes"]) == {
        "known", "inferable", "searchable", "tool-executable", "verifiable"
    }, "REFUSE_DECOMPOSITION_LEAF_DRIFT")

    require(obs["exact_subject_required"], "REFUSE_NON_EXACT_SUBJECT")
    require(obs["shared_corpus_required"], "REFUSE_PRIVATE_RUNTIME_REALITY")
    require(obs["corpus_digest"] == "BLAKE3", "REFUSE_CORPUS_DIGEST_DRIFT")
    require(not obs["foreign_corpus_has_standing"], "REFUSE_FOREIGN_CORPUS_STANDING")

    require(manufacture["operator_symbol"] == "mu", "REFUSE_OPERATOR_DRIFT")
    require(manufacture["construct_only"], "REFUSE_NON_CONSTRUCT_MANUFACTURE")
    for key in (
        "runtime_query_text",
        "runtime_executable_ir",
        "runtime_prompt_instructions",
        "runtime_shell_instructions",
        "runtime_dynamic_query_fragments",
    ):
        require(not manufacture[key], f"REFUSE_{key.upper()}")
    require(manufacture["artifact_must_follow_equation"], "REFUSE_ARTIFACT_OUTSIDE_EQUATION")

    require(interaction["standing_precedes_interaction"], "REFUSE_INTERACTION_BEFORE_STANDING")
    require(interaction["first_handshake_evidence"] == "OCEL_V2", "REFUSE_NON_OCEL_HANDSHAKE")
    require(interaction["requires_process_conformance"], "REFUSE_PROCESS_BLIND_HANDSHAKE")
    require(interaction["requires_exact_corpus_correspondence"], "REFUSE_CORPUS_MISMATCH")
    require(interaction["requires_exact_part_correspondence"], "REFUSE_PART_MISMATCH")
    require(interaction["mismatch_behavior"] == "REFUSE_NO_INTERACTION", "REFUSE_MISMATCH_FALLBACK")

    require(process["carrier"] == "OCEL_V2", "REFUSE_PROCESS_CARRIER_DRIFT")
    require(process["process_is_state_evidence"], "REFUSE_PROCESS_STATE_SEPARATION")
    require(process["process_is_creation_standing"], "REFUSE_PROCESS_STANDING_SEPARATION")
    require(process["history_is_not_merely_audit_log"], "REFUSE_AUDIT_LOG_REDUCTION")

    algebra = process["algebra"]
    geometry = process["geometry"]
    calculus = process["calculus"]
    require(algebra["enabled"] and algebra["lawful_composition"], "REFUSE_ALGEBRA_DISABLED")
    require(algebra["undefined_compositions_refuse"], "REFUSE_UNDEFINED_COMPOSITION")
    require(geometry["enabled"] and geometry["route_is_part_of_subject"], "REFUSE_GEOMETRY_DISABLED")
    require(geometry["creation_key_is_process_geometry"], "REFUSE_SCALAR_CREATION_KEY")
    require(not geometry["endpoint_equality_does_not_imply_standing_equality"] is False,
            "REFUSE_ENDPOINT_ONLY_STANDING")
    require(calculus["enabled"] and calculus["lawful_flow_required"], "REFUSE_CALCULUS_DISABLED")
    require(calculus["first_derivative_conformance"], "REFUSE_VELOCITY_BLINDNESS")
    require(calculus["second_derivative_conformance"], "REFUSE_ACCELERATION_BLINDNESS")
    require(calculus["integral_process_invariants"], "REFUSE_PATH_INTEGRAL_BLINDNESS")

    require(wasm["role"] == "signed_interchangeable_part", "REFUSE_WASM_ROLE_DRIFT")
    require(wasm["exact_part_digest"] == "BLAKE3", "REFUSE_PART_DIGEST_DRIFT")
    require(wasm["signed_part_required"], "REFUSE_UNSIGNED_PART")
    require(not wasm["source_semantics_required_at_runtime"], "REFUSE_RUNTIME_SOURCE_SEMANTICS")
    require(not wasm["manufacturing_history_required_inside_part"], "REFUSE_FACTORY_IN_PART")
    require(wasm["zero_cost_rust_target"], "REFUSE_ZERO_COST_TARGET_DISABLED")
    require(wasm["branchless_runtime_target"], "REFUSE_BRANCHLESS_TARGET_DISABLED")
    require(wasm["embedded_strings_policy"] == "IMPORT_EXPORT_ONLY", "REFUSE_STRING_SURFACE_DRIFT")
    require(not wasm["ambient_host_capabilities"], "REFUSE_AMBIENT_HOST_CAPABILITY")

    require(dispatch["wire_width_bits"] == 8, "REFUSE_SELECTOR_WIDTH")
    require(dispatch["minimum_selector"] == 0 and dispatch["maximum_selector"] == 255,
            "REFUSE_SELECTOR_RANGE")
    require(dispatch["selector_meaning"] == "pre_admitted_execution_capsule", "REFUSE_DYNAMIC_SELECTOR_MEANING")
    require(dispatch["exhaustive_selector_space"], "REFUSE_NON_EXHAUSTIVE_SELECTOR")
    for key in ("selector_transports_query_text", "selector_transports_code", "selector_transports_ir"):
        require(not dispatch[key], f"REFUSE_{key.upper()}")
    for key in (
        "selector_may_bind_wasm_part",
        "selector_may_bind_construct",
        "selector_may_bind_graph_view",
        "selector_may_bind_policy",
        "selector_may_bind_receipt_shape",
    ):
        require(dispatch[key], f"REFUSE_{key.upper()}_DISABLED")

    for key in (
        "behavioral_equivalence_implies_standing",
        "artifact_possession_implies_standing",
        "architecture_knowledge_implies_authority",
        "modified_artifact_preserves_standing",
        "modified_process_preserves_standing",
        "modified_corpus_preserves_standing",
    ):
        require(not standing[key], f"REFUSE_{key.upper()}")

    require(hie["enabled"], "REFUSE_HIE_DISABLED")
    require(hie["meaning_lives_in_cross_dimensional_relations"], "REFUSE_PROJECTION_ONLY_MEANING")
    require(not hie["single_projection_is_authoritative"], "REFUSE_SINGLE_PROJECTION_AUTHORITY")
    require(not hie["master_rosetta_stone_required"], "REFUSE_ROSETTA_RUNTIME_DEPENDENCY")
    require(hie["manufacture_may_be_non_injective"], "REFUSE_INVERTIBLE_MANUFACTURE_ASSUMPTION")
    require(hie["runtime_artifact_need_not_encode_factory"], "REFUSE_FACTORY_DISCLOSURE_REQUIREMENT")
    require(len(set(hie["projections"])) == len(hie["projections"]) >= 9, "REFUSE_HIE_DIMENSION_COLLAPSE")

    require(security["attack_surface_model"] == "LAWFUL_REACHABILITY", "REFUSE_SECURITY_MODEL_DRIFT")
    require(not security["foreign_instruction_language"], "REFUSE_FOREIGN_INSTRUCTION_LANGUAGE")
    require(not security["probing_can_create_new_transition"], "REFUSE_PROBE_CREATED_TRANSITION")
    require(not security["attacker_intelligence_can_create_new_transition"], "REFUSE_INTELLIGENCE_CREATED_TRANSITION")
    require(security["red_team_goal_must_be_reachable_inside_constitution"], "REFUSE_UNBOUNDED_RED_TEAM_MODEL")
    require(security["counterexample_is_constitutional_evidence"], "REFUSE_COUNTEREXAMPLE_ERASURE")

    require(vision["style"] == "BORING_BY_DESIGN", "REFUSE_CYBERPUNK_RUNTIME")
    require(vision["integration_requires_conformance_before_interaction"], "REFUSE_NEGOTIATE_THEN_CONFORM")
    require(not vision["runtime_semantic_negotiation"], "REFUSE_RUNTIME_SEMANTIC_NEGOTIATION")
    require(vision["works_or_does_not_participate"], "REFUSE_PARTIAL_UNPROVEN_INTERACTION")

    return {
        "profile": profile["id"],
        "standing": profile["standing"],
        "selector_count": dispatch["maximum_selector"] - dispatch["minimum_selector"] + 1,
        "hie_dimensions": len(hie["projections"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=pathlib.Path, default=DEFAULT_PROFILE)
    args = parser.parse_args()
    try:
        result = verify(args.path)
    except (KeyError, TypeError, tomllib.TOMLDecodeError, Refusal) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    print(
        "ADMITTED: "
        f"profile={result['profile']} standing={result['standing']} "
        f"selectors={result['selector_count']} hie_dimensions={result['hie_dimensions']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
