#!/usr/bin/env python3
"""Non-actuating Factory E conformance checker.

Reads one claim (JSON), validates it against the schema subset used by
schemas/factory-e-conformance.schema.json, then applies the semantic laws.
No network, no writes. Exit 0 = conformant, 1 = typed refusal.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schemas" / "factory-e-conformance.schema.json"
QUAL_TERMS = ["ExactSubject", "Provenance", "CanonicalSemantics", "AuthorityBound", "ConsequenceBound", "IndependentObservation", "Receipt", "ReplaySafe", "Falsifiers", "Migration"]
CORE = ["QMX", "NHS", "CANON", "CSEP", "IOBS", "NAREP", "MXNEG", "CHEST", "ACD", "HARD", "CHIC", "SMAN", "XCAP", "PROF"]


class Refusal(Exception):
    def __init__(self, code, detail=""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


def _validate(inst, sch, root, path="$"):
    """Minimal JSON Schema validator: type/enum/const/required/properties/items/pattern/minLength/$ref."""
    if "$ref" in sch:
        node = root
        for part in sch["$ref"].lstrip("#/").split("/"):
            node = node[part]
        return _validate(inst, node, root, path)
    if "const" in sch and inst != sch["const"]:
        raise Refusal("SCHEMA_INVALID", f"{path} != {sch['const']!r}")
    if "enum" in sch and inst not in sch["enum"]:
        raise Refusal("SCHEMA_INVALID", f"{path} not in enum")
    t = sch.get("type")
    checks = {"object": dict, "array": list, "string": str, "boolean": bool, "number": (int, float)}
    if t and (not isinstance(inst, checks[t]) or (t == "number" and isinstance(inst, bool))):
        raise Refusal("SCHEMA_INVALID", f"{path} not {t}")
    if isinstance(inst, str):
        if len(inst) < sch.get("minLength", 0):
            raise Refusal("SCHEMA_INVALID", f"{path} too short")
        if "pattern" in sch and not re.search(sch["pattern"], inst):
            raise Refusal("SCHEMA_INVALID", f"{path} pattern")
    if isinstance(inst, dict):
        for k in sch.get("required", []):
            if k not in inst:
                raise Refusal("SCHEMA_INVALID", f"{path}.{k} missing")
        props = sch.get("properties", {})
        if sch.get("additionalProperties") is False:
            for k in inst:
                if k not in props:
                    raise Refusal("SCHEMA_INVALID", f"{path}.{k} unexpected")
        for k, v in inst.items():
            if k in props:
                _validate(v, props[k], root, f"{path}.{k}")
    if isinstance(inst, list) and "items" in sch:
        for i, v in enumerate(inst):
            _validate(v, sch["items"], root, f"{path}[{i}]")


def _ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        raise Refusal("SCHEMA_INVALID", f"bad timestamp {s!r}")


def check(claim, now=None):
    schema = json.loads(SCHEMA.read_text())
    _validate(claim, schema, schema)
    subj = claim["subject"]

    hz = claim["evidence_horizon"]
    obs_at = _ts(hz["observed_at"])
    if "expires_at" in hz and now is not None:
        if _ts(hz["expires_at"]) <= _ts(now) or obs_at > _ts(now):
            raise Refusal("EVIDENCE_HORIZON_EXPIRED", hz["expires_at"])

    seen = {}
    for law in claim["laws"]:
        if law["id"] in seen:
            raise Refusal("DUPLICATE_LAW", law["id"])
        seen[law["id"]] = law
    missing = [i for i in CORE if i not in seen]
    if missing:
        raise Refusal("MISSING_LAW", ",".join(missing))

    for law in seen.values():
        for ev in law["evidence"]:
            if ev["subject"] != subj:
                raise Refusal("STALE_OR_FOREIGN_SUBJECT", f"{law['id']}:{ev['ref']}")
        if law["standing"] == "ALIVE":
            ev = law["evidence"]
            if not any(e["kind"] == "EXECUTED" for e in ev):
                raise Refusal("ALIVE_WITHOUT_EXECUTION", law["id"])
            ok = [e for e in ev if e["kind"] == "VERIFIED" and e.get("observer") and e.get("producer")]
            if not any(e["observer"] != e["producer"] for e in ok):
                raise Refusal("SELF_CERTIFIED", law["id"])

    owners = {}
    for t in claim["terms"]:
        if t["term"] in owners and owners[t["term"]] != t["owner"]:
            raise Refusal("HIDDEN_SEMANTICS", f"term {t['term']} has multiple owners")
        owners[t["term"]] = t["owner"]

    for c in claim["consequences"]:
        if c["class"] == "DO" and not (c.get("authority") and c.get("receipt")):
            raise Refusal("CONSEQUENCE_UNAUTHORIZED", c["id"])

    if claim["replay"]["actuating"]:
        raise Refusal("ACTUATING_REPLAY")

    for p in claim.get("profiles", []):
        if p.get("overrides"):
            raise Refusal("PROFILE_WEAKENS_CORE", f"{p['id']} overrides {p['overrides']}")
        if p["id"] == "fibo":
            for term in p.get("profile_terms", []):
                if not owners.get(term, "").startswith("fibo:"):
                    raise Refusal("HIDDEN_SEMANTICS", f"fibo term {term} lacks fibo: owner")
    _semantic_laws(claim, seen)
    return {"conformant": True, "subject": subj, "laws": len(seen)}


def _semantic_laws(claim, laws):
    """Executable checks for MXNEG, CHEST, ACD, HARD, CHIC, XCAP, SMAN (all optional-input, additive)."""
    for c in claim.get("changes", []):
        if c["net_value"] <= 0:
            raise Refusal("NEGATIVE_VALUE_CHANGE", c["id"])
    for r in claim.get("constraint_removals", []):
        if not r["origin_observed"] or not r.get("receipt"):
            raise Refusal("CHESTERTON_VIOLATION", r["id"])
    for d in claim.get("distilled_constraints", []):
        if not d["attempt_observed"]:
            raise Refusal("VACUOUS_COURT", d["id"])
        if d["violation_observed"]:
            raise Refusal("VIOLATION_OBSERVED", d["id"])
    for h in claim.get("hardening", []):
        fixture = (ROOT / h["fixture"]).resolve()
        if ROOT not in fixture.parents or not fixture.is_file():
            raise Refusal("UNHARDENED_FAILURE", h["failure"])
    if laws["CHIC"]["standing"] == "ALIVE":
        q = claim.get("qualification", {})
        if not all(q.get(k) is True for k in QUAL_TERMS):
            raise Refusal("CHICAGO_NOT_CONJUNCTIVE", ",".join(k for k in QUAL_TERMS if q.get(k) is not True))
    for x in claim.get("external_capabilities", []):
        if not x["requalified"]:
            raise Refusal("EXTERNAL_NOT_REQUALIFIED", x["id"])


def main(argv):
    if len(argv) != 2:
        print("usage: factory_e_conformance.py CLAIM.json", file=sys.stderr)
        return 2
    try:
        print(json.dumps(check(json.loads(Path(argv[1]).read_text())), sort_keys=True))
        return 0
    except Refusal as r:
        print(json.dumps({"conformant": False, "refusal": r.code, "detail": str(r)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
