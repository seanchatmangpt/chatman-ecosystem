"""Terminality policy: which terminal states each requirement admits (RFC-0004 §38, §47, §48, §55).

``policy/<release>/terminality.json`` has one row per requirement id (AC-01..AC-19,
F-01..F-14). A row names the success state the requirement needs, the terminal states it
admits, the evidence and authority it needs, the standing ceiling a PASS certifies, and
the RFC anchor and phrase that ground it. It also carries ``acceptance_sha256``, the
sha256 of the requirement's acceptance text in ``requirements.json``.

A row is a *relaxation* when it admits a state outside ``SUCCESS_STATES``, such as a typed
SUPERSEDED/BLOCKED/UNSUPPORTED/REFUSED disposition. A relaxation is lawful only when:

* the pinned RFC import hashes to the policy's ``rfc_import.sha256``;
* ``rfc_phrase`` is a literal substring of the ``rfc_anchor`` section of that import and,
  for the §48 / §47 anchors, of the requirement's own line there (``AC-02 ...`` /
  ``3. ...``), so one requirement cannot borrow another's terminality;
* no other relaxed row cites the same anchor and phrase;
* the phrase names terminality (``RELAXATION_MARKERS``);
* the admitted states are all RFC §38 dispositions;
* the ceiling is ``TERMINAL``, never ``ALIVE``.

Otherwise the row is refused with ``POLICY_RELAXATION_UNGROUNDED``. Other refusals:

* ``TERMINALITY_POLICY_MISSING``: the policy file is absent, unreadable or for another
  release.
* ``POLICY_COVERAGE_GAP``: a requirement has no row, or a row is extra, duplicated or
  malformed.
* ``ACCEPTANCE_DRIFT``: the acceptance text changed without the policy moving with it.

This module is pure: it reads the policy file and nothing else. It never spawns a
process and never touches the network.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .model import REFUSED, ReqState
from .requirements import premise_sections

POLICY_ROOT = Path(__file__).resolve().parent / "policy"
POLICY_FILE = "terminality.json"
SCHEMA_POLICY = "https://chatman.dev/root-crown/policy/terminality/v1"
SUCCESS_STATES = ("ALIVE", "FINAL")
# RFC §38 non-success dispositions (terminal only when typed; evidence.typing_gaps).
TYPED_STATES = ("SUPERSEDED", "BLOCKED", "UNSUPPORTED", "REFUSED")
CEILINGS = ("ALIVE", "TERMINAL")
# A relaxation phrase must name terminality itself, not merely occur in the RFC.
RELAXATION_MARKERS = ("terminal", "typed_blocker", "remains UNKNOWN")
ROW_FIELDS = (
    "id",
    "required_success_state",
    "allowed_terminal_states",
    "evidence_required",
    "authority_required",
    "standing_ceiling",
    "rfc_anchor",
    "rfc_phrase",
    "acceptance_sha256",
)
POLICY_CODES = (
    "TERMINALITY_POLICY_MISSING",
    "POLICY_COVERAGE_GAP",
    "POLICY_RELAXATION_UNGROUNDED",
    "ACCEPTANCE_DRIFT",
)


class PolicyMissing(Exception):
    """The policy file for a release is absent, unreadable or names another release."""


@dataclass(frozen=True)
class Row:
    id: str
    required_success_state: str
    allowed_terminal_states: tuple[str, ...]
    evidence_required: str
    authority_required: str
    standing_ceiling: str
    rfc_anchor: str
    rfc_phrase: str
    acceptance_sha256: str

    @property
    def relaxed(self) -> tuple[str, ...]:
        """Admitted states beyond success (non-empty = a relaxation)."""
        return tuple(s for s in self.allowed_terminal_states if s not in SUCCESS_STATES)

    def admits(self, state: str | None) -> bool:
        return state in self.allowed_terminal_states


@dataclass(frozen=True)
class Policy:
    release: str
    path: str
    rfc_import_path: str
    rfc_import_sha256: str
    rows: tuple[dict[str, Any], ...]

    def raw(self, rid: str) -> list[dict[str, Any]]:
        return [r for r in self.rows if isinstance(r, dict) and r.get("id") == rid]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def policy_path(release: str, root: Path = POLICY_ROOT) -> Path:
    return root / release / POLICY_FILE


def load_policy(release: str, root: Path = POLICY_ROOT) -> Policy:
    """The committed policy of ``release``; raises ``PolicyMissing`` (TERMINALITY_POLICY_MISSING)."""
    path = policy_path(release, root)
    if not path.is_file():
        raise PolicyMissing(f"absent:{release}/{POLICY_FILE}")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PolicyMissing(f"unreadable:{release}/{POLICY_FILE}:{type(exc).__name__}") from exc
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA_POLICY:
        raise PolicyMissing(f"schema:{release}/{POLICY_FILE}")
    if doc.get("release") != release:
        raise PolicyMissing(f"release:{release}/{POLICY_FILE} names {doc.get('release')!r}")
    rfc = doc.get("rfc_import")
    rows = doc.get("rows")
    if not isinstance(rfc, dict) or not isinstance(rows, list):
        raise PolicyMissing(f"shape:{release}/{POLICY_FILE}")
    return Policy(
        release=release,
        path=f"{release}/{POLICY_FILE}",
        rfc_import_path=str(rfc.get("path", "")),
        rfc_import_sha256=str(rfc.get("sha256", "")),
        rows=tuple(rows),
    )


def own_line(rid: str, anchor: str, section: str) -> str | None:
    """The requirement's own line in §48 (``AC-NN ...``) or §47 (``N. ...``); None for other anchors."""
    if anchor == "§48" and rid.startswith("AC-"):
        pattern = rf"^{re.escape(rid)} .*$"
    elif anchor == "§47" and rid.startswith("F-") and rid[2:].isdigit():
        pattern = rf"^{int(rid[2:])}\. .*$"
    else:
        return None
    match = re.search(pattern, section, re.MULTILINE)
    return match.group(0) if match else ""


def _malformed(row: dict[str, Any]) -> list[str]:
    bad = []
    for key in ROW_FIELDS:
        value = row.get(key)
        if key == "allowed_terminal_states":
            if not isinstance(value, list) or not value or not all(isinstance(s, str) and s for s in value):
                bad.append(key)
        elif not isinstance(value, str) or not value.strip():
            bad.append(key)
    return bad


def _to_row(raw: dict[str, Any]) -> Row:
    return Row(**{k: (tuple(raw[k]) if k == "allowed_terminal_states" else raw[k]) for k in ROW_FIELDS})


def row_refusals(
    raw: dict[str, Any], acceptance: str, rfc_text: str, policy: Policy, import_sha256: str | None
) -> tuple[Row | None, list[tuple[str, str]]]:
    """(row, [(code, detail)]) for one policy row against its requirement and the pinned RFC."""
    rid = str(raw.get("id"))
    bad = _malformed(raw)
    if bad:
        return None, [("POLICY_COVERAGE_GAP", f"{rid}:malformed:{'+'.join(bad)}")]
    row = _to_row(raw)
    out: list[tuple[str, str]] = []
    if sha256_text(acceptance) != row.acceptance_sha256:
        out.append(
            ("ACCEPTANCE_DRIFT", f"{rid}:acceptance sha256={sha256_text(acceptance)} policy={row.acceptance_sha256}")
        )
    ungrounded: list[str] = []
    if row.required_success_state not in SUCCESS_STATES or not row.admits(row.required_success_state):
        ungrounded.append(f"required_success_state={row.required_success_state}")
    foreign = sorted(set(row.allowed_terminal_states) - set(SUCCESS_STATES) - set(TYPED_STATES))
    if foreign:
        ungrounded.append(f"non-terminal states {','.join(foreign)} (RFC §38)")
    if row.standing_ceiling not in CEILINGS:
        ungrounded.append(f"standing_ceiling={row.standing_ceiling}")
    if row.relaxed:
        if row.standing_ceiling != "TERMINAL":
            ungrounded.append(f"relaxation {','.join(row.relaxed)} claims ceiling {row.standing_ceiling}")
        text_sha = sha256_text(rfc_text)
        if text_sha != policy.rfc_import_sha256 or (import_sha256 is not None and import_sha256 != text_sha):
            ungrounded.append(
                f"rfc import sha256={text_sha} policy={policy.rfc_import_sha256} IMPORTS.json={import_sha256}"
            )
        section = premise_sections(rfc_text).get(row.rfc_anchor)
        if section is None:
            ungrounded.append(f"anchor {row.rfc_anchor} absent from the RFC import")
        elif row.rfc_phrase not in section:
            ungrounded.append(f"phrase {row.rfc_phrase!r} not in {row.rfc_anchor}")
        elif (line := own_line(rid, row.rfc_anchor, section)) is not None and row.rfc_phrase not in line:
            ungrounded.append(f"phrase {row.rfc_phrase!r} not on {rid}'s own {row.rfc_anchor} line")
        if not any(marker in row.rfc_phrase for marker in RELAXATION_MARKERS):
            ungrounded.append(f"phrase {row.rfc_phrase!r} names no terminality marker")
    elif row.standing_ceiling != "ALIVE":
        ungrounded.append(f"success-only row claims ceiling {row.standing_ceiling}")
    if ungrounded:
        out.append(("POLICY_RELAXATION_UNGROUNDED", f"{rid}:" + ";".join(ungrounded)))
    return row, out


def validate(
    policy: Policy | None,
    missing: str | None,
    requirement_rows: Iterable[dict[str, Any]],
    rfc_text: str,
    import_sha256: str | None,
) -> list[str]:
    """Whole-document admission: ``REFUSED:<CODE>:<detail>`` strings (sorted, unique)."""
    if policy is None:
        return [f"REFUSED:TERMINALITY_POLICY_MISSING:{missing or 'absent'}"]
    refusals: list[str] = []
    rows = [r for r in requirement_rows if isinstance(r, dict) and isinstance(r.get("id"), str)]
    declared = {r["id"] for r in rows}
    ids = [r.get("id") if isinstance(r, dict) else None for r in policy.rows]
    for rid in sorted({i for i in ids if ids.count(i) > 1}, key=str):
        refusals.append(f"REFUSED:POLICY_COVERAGE_GAP:{rid}:duplicate-row")
    for rid in sorted({str(i) for i in ids} - declared):
        refusals.append(f"REFUSED:POLICY_COVERAGE_GAP:{rid}:not-a-requirement")
    citations: dict[tuple[str, str], list[str]] = {}
    for raw in policy.rows:
        if isinstance(raw, dict) and not _malformed(raw) and _to_row(raw).relaxed:
            citations.setdefault((raw["rfc_anchor"], raw["rfc_phrase"]), []).append(raw["id"])
    for (anchor, phrase), cited_by in sorted(citations.items()):
        if len(cited_by) > 1:
            refusals.append(
                f"REFUSED:POLICY_RELAXATION_UNGROUNDED:{','.join(sorted(cited_by))}:"
                f"one grounding {anchor} {phrase!r} cited by several relaxations"
            )
    for req in rows:
        raws = policy.raw(req["id"])
        if not raws:
            refusals.append(f"REFUSED:POLICY_COVERAGE_GAP:{req['id']}:no-policy-row")
            continue
        _, problems = row_refusals(raws[0], str(req.get("acceptance", "")), rfc_text, policy, import_sha256)
        refusals += [f"REFUSED:{code}:{detail}" for code, detail in problems]
    return sorted(set(refusals))


def admit(
    policy: Policy | None,
    missing: str | None,
    rid: str,
    acceptance: str,
    rfc_text: str,
    import_sha256: str | None,
) -> tuple[Row | None, ReqState | None]:
    """(row, None) when the requirement's row is admitted, else (None, typed REFUSED)."""
    if policy is None:
        return None, REFUSED("TERMINALITY_POLICY_MISSING", missing or "absent")
    raws = policy.raw(rid)
    if len(raws) != 1:
        return None, REFUSED("POLICY_COVERAGE_GAP", f"{rid}:{len(raws)} policy rows in {policy.path}")
    row, problems = row_refusals(raws[0], acceptance, rfc_text, policy, import_sha256)
    if problems:
        code, detail = problems[0]
        return None, REFUSED(code, detail)
    return row, None
