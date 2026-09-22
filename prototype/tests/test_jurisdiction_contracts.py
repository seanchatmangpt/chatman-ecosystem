"""PR-3 slice: machine-enforced jurisdiction refusal contracts.

Makes the AGENTS.md "Jurisdiction table" mechanically load-bearing instead of
prose: the in-code JURISDICTION_TABLE and MUST_NOT_OWN registry must exactly
match the constitution's table (doc/code conformance), and every "Must not
own" cell must produce a real refusal (REFUSED_JURISDICTION_FORBIDDEN).

Real, state-based tests: they parse the actual AGENTS.md on disk and call the
actual registry functions. No mocks, no patched imports.
"""

import os
import re

import pytest

import jurisdiction
from jurisdiction import JURISDICTION_TABLE, MUST_NOT_OWN, JurisdictionViolation

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AGENTS_MD = os.path.join(REPO_ROOT, "AGENTS.md")

# Doc symbols -> registry coordinate names (jurisdiction.py vocabulary).
SYMBOL_MAP = {
    "P": "P",
    "Γ": "Gamma",
    "Ω": "Omega",
    "B": "B",
    "τ": "tau",
    "J": "J",
    "A": "A",
    "R": "R",
    "μ": "Mu",
    "ΔZ": "DeltaZ",
    # The chatman-ecosystem row writes these without parentheses and with
    # mixed case: "Meta-A, meta-R, ontology contracts".
    "Meta-A": "A",
    "meta-A": "A",
    "Meta-R": "R",
    "meta-R": "R",
}


def _parse_agents_md_jurisdiction_table():
    """Parses the '## Jurisdiction table' markdown rows from AGENTS.md.

    Returns {repo: (owns_symbols, must_not_own_tags)} where owns_symbols is a
    set of registry coordinate names and must_not_own_tags is the verbatim
    comma-split list from the doc. Fails closed: a row that yields no
    coordinate symbols is a parse error, never a silent skip.
    """
    with open(AGENTS_MD, encoding="utf-8") as handle:
        text = handle.read()

    section = text.split("## Jurisdiction table", 1)[1]
    section = section.split("## ", 1)[0]

    table = {}
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 3 or cells[0] in ("Repo", "---", ""):
            continue
        if set(cells[0]) <= {"-", ":", " "}:
            continue
        repo, owns_cell, forbidden_cell = cells
        # "chatman-ecosystem (this repo)" -> "chatman-ecosystem".
        repo = re.sub(r"\s*\([^)]*\)\s*$", "", repo)

        match = re.search(r"\(([^)]*)\)", owns_cell)
        scope = match.group(1) if match else owns_cell
        symbols = set()
        for token in [t.strip() for t in scope.split(",")]:
            if not token:
                continue
            if " " in token:
                # Descriptive gloss (e.g. "ontology contracts"), not a
                # coordinate symbol; coordinates are single-token symbols.
                if match:
                    raise AssertionError(
                        f"unexpected gloss {token!r} inside the parenthesized "
                        f"coordinate list of AGENTS.md row {repo!r}"
                    )
                continue
            if token not in SYMBOL_MAP:
                raise AssertionError(
                    f"unmapped jurisdiction symbol {token!r} in AGENTS.md row {repo!r}"
                )
            symbols.add(SYMBOL_MAP[token])
        if not symbols:
            raise AssertionError(f"no jurisdiction symbols parsed for row {repo!r}")

        forbidden = [tag.strip() for tag in forbidden_cell.split(",") if tag.strip()]
        table[repo] = (symbols, forbidden)
    return table


def test_agents_md_table_covers_exactly_the_registry_repos():
    table = _parse_agents_md_jurisdiction_table()
    assert len(table) == 18
    assert set(table) == set(JURISDICTION_TABLE)


def test_allowed_coordinates_match_agents_md_exactly():
    table = _parse_agents_md_jurisdiction_table()
    for repo, (symbols, _forbidden) in table.items():
        assert set(JURISDICTION_TABLE[repo]) == symbols, (
            f"JURISDICTION_TABLE[{repo!r}] drifted from AGENTS.md: "
            f"code={sorted(JURISDICTION_TABLE[repo])!r} doc={sorted(symbols)!r}"
        )


def test_must_not_own_registry_matches_agents_md_exactly():
    table = _parse_agents_md_jurisdiction_table()
    assert set(MUST_NOT_OWN) == set(table)
    for repo, (_symbols, forbidden) in table.items():
        assert MUST_NOT_OWN[repo] == forbidden, (
            f"MUST_NOT_OWN[{repo!r}] drifted from AGENTS.md: "
            f"code={MUST_NOT_OWN[repo]!r} doc={forbidden!r}"
        )


def test_check_forbidden_refuses_a_must_not_own_capability():
    # beam4pm's contract forbids exactly one capability: DO.
    with pytest.raises(JurisdictionViolation) as excinfo:
        jurisdiction.check_forbidden("beam4pm", "DO")
    assert "REFUSED_JURISDICTION_FORBIDDEN" in str(excinfo.value)
    assert "beam4pm" in str(excinfo.value)


def test_check_forbidden_allows_capabilities_outside_the_contract():
    # Planning is not in beam4pm's must-not-own list: no refusal.
    assert jurisdiction.check_forbidden("beam4pm", "Planning") is True


def test_check_forbidden_is_fail_closed_for_unknown_components():
    # A component with no admitted contract refuses every capability.
    with pytest.raises(JurisdictionViolation) as excinfo:
        jurisdiction.check_forbidden("unknown-component", "B")
    assert "REFUSED_JURISDICTION_UNKNOWN_COMPONENT" in str(excinfo.value)


def test_guard_enforces_the_forbidden_capability_too():
    @jurisdiction.guard("autofde-lab")
    def act_on(z_coordinate, capability=None):
        return z_coordinate

    # autofde-lab's must-not-own is "Production authority".
    assert act_on("B", capability="Planning") == "B"
    with pytest.raises(JurisdictionViolation) as excinfo:
        act_on("B", capability="Production authority")
    assert "REFUSED_JURISDICTION_FORBIDDEN" in str(excinfo.value)


def test_check_forbidden_refuses_xaas_minting_authority():
    """The 2026-09-21 cycle's new contract: xaas coordinates the loop but must
    never mint Authority or own the canonical human ontology -- planner and
    orchestrator output has no ambient execution authority, which is xaas's
    own repo law enforced here in the meta-governance registry."""
    with pytest.raises(JurisdictionViolation) as excinfo:
        jurisdiction.check_forbidden("xaas", "minting Authority")
    assert "REFUSED_JURISDICTION_FORBIDDEN" in str(excinfo.value)
    assert "xaas" in str(excinfo.value)


def test_all_five_loop_participants_are_now_admitted():
    """The five participants added in the 2026-09-21 cycle must be known
    components (fail-closed only applies to the genuinely unknown)."""
    for component in ("xaas", "ggen_igniter", "zcode-cli", "ash_surface", "dfcm-autonomous"):
        assert jurisdiction.check_forbidden(component, "anything-not-forbidden") is True
        assert jurisdiction.check_jurisdiction(component, JURISDICTION_TABLE[component][0]) is True
