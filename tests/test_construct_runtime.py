from __future__ import annotations

import copy
import importlib.util
import pathlib
import tempfile
import tomllib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = ROOT / "scripts" / "verify_construct_runtime.py"
PROFILE = ROOT / "catalog" / "construct-runtime.toml"

spec = importlib.util.spec_from_file_location("verify_construct_runtime", SPEC)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def dump_toml_for_fixture(data: dict) -> str:
    """Minimal deterministic TOML writer for the bounded negative fixtures."""
    lines: list[str] = []

    def emit_table(prefix: str, table: dict) -> None:
        scalars: list[tuple[str, object]] = []
        nested: list[tuple[str, dict]] = []
        for key, value in table.items():
            if isinstance(value, dict):
                nested.append((key, value))
            else:
                scalars.append((key, value))
        if prefix:
            lines.append(f"[{prefix}]")
        for key, value in scalars:
            if isinstance(value, bool):
                rendered = "true" if value else "false"
            elif isinstance(value, int):
                rendered = str(value)
            elif isinstance(value, str):
                rendered = repr(value).replace("'", '"')
            elif isinstance(value, list):
                rendered = "[" + ", ".join(repr(v).replace("'", '"') for v in value) + "]"
            else:
                raise TypeError(value)
            lines.append(f"{key} = {rendered}")
        if scalars:
            lines.append("")
        for key, value in nested:
            emit_table(f"{prefix}.{key}" if prefix else key, value)

    emit_table("", data)
    return "\n".join(lines)


class ConstructRuntimeProfileTests(unittest.TestCase):
    def load(self) -> dict:
        with PROFILE.open("rb") as fh:
            return tomllib.load(fh)

    def verify_mutation_refuses(self, mutate, code: str) -> None:
        data = copy.deepcopy(self.load())
        mutate(data)
        with tempfile.TemporaryDirectory() as td:
            fixture = pathlib.Path(td) / "mutated.toml"
            fixture.write_text(dump_toml_for_fixture(data), encoding="utf-8")
            with self.assertRaisesRegex(module.Refusal, code):
                module.verify(fixture)

    def test_canonical_profile_is_admitted_as_candidate(self) -> None:
        result = module.verify(PROFILE)
        self.assertEqual(result["standing"], "CANDIDATE")
        self.assertEqual(result["selector_count"], 256)
        self.assertGreaterEqual(result["hie_dimensions"], 9)

    def test_transporting_query_text_is_refused(self) -> None:
        self.verify_mutation_refuses(
            lambda d: d["dispatch"].__setitem__("selector_transports_query_text", True),
            "REFUSE_SELECTOR_TRANSPORTS_QUERY_TEXT",
        )

    def test_non_ocel_first_handshake_is_refused(self) -> None:
        self.verify_mutation_refuses(
            lambda d: d["interaction"].__setitem__("first_handshake_evidence", "API_KEY"),
            "REFUSE_NON_OCEL_HANDSHAKE",
        )

    def test_foreign_corpus_standing_is_refused(self) -> None:
        self.verify_mutation_refuses(
            lambda d: d["observation"].__setitem__("foreign_corpus_has_standing", True),
            "REFUSE_FOREIGN_CORPUS_STANDING",
        )

    def test_selector_space_wider_than_one_byte_is_refused(self) -> None:
        self.verify_mutation_refuses(
            lambda d: d["dispatch"].__setitem__("wire_width_bits", 16),
            "REFUSE_SELECTOR_WIDTH",
        )

    def test_runtime_source_semantics_are_refused(self) -> None:
        self.verify_mutation_refuses(
            lambda d: d["wasm"].__setitem__("source_semantics_required_at_runtime", True),
            "REFUSE_RUNTIME_SOURCE_SEMANTICS",
        )

    def test_scalar_creation_key_replacing_process_geometry_is_refused(self) -> None:
        self.verify_mutation_refuses(
            lambda d: d["process"]["geometry"].__setitem__("creation_key_is_process_geometry", False),
            "REFUSE_SCALAR_CREATION_KEY",
        )

    def test_behavioral_clone_cannot_inherit_standing(self) -> None:
        self.verify_mutation_refuses(
            lambda d: d["standing"].__setitem__("behavioral_equivalence_implies_standing", True),
            "REFUSE_BEHAVIORAL_EQUIVALENCE_IMPLIES_STANDING",
        )


if __name__ == "__main__":
    unittest.main()
