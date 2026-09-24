#!/usr/bin/env python3
"""Recorded corrections of CE23 extraction JSON (lane CE-INTAKE, wave CE0).

The extraction JSON is the one LLM edge of the CE23 first mile (raw O,
`candidates/raw/<unit>.extract.json`, byte-identical to what the extractor
wrote). A correction never edits that file: it is one entry of
`candidates/corrections.json`, and the extraction that feeds
`prose_spans.py emit` (`candidates/<unit>.extract.json`) is GENERATED here as
apply(raw, corrections). `check` recomputes every generated extraction and
refuses a hand edit, a stale guard or an unknown unit.

  apply --raw-dir DIR --corrections JSON --out-dir DIR
  check --raw-dir DIR --corrections JSON --out-dir DIR

A correction entry: {unit, index, quote, field, from, to, reason}. `quote`
must equal the raw item's quote (index drift is refused), `from` must equal
the raw value (null = absent), `to` replaces it (null = delete the key).
Only `required_by` and `boundary_class` may be corrected: a quote, kind or
statement correction would change what the prose is claimed to say, and must
go back through the extractor instead. Output: indent=1, sorted keys,
ensure_ascii=False, trailing newline (the raw extractor's own form).

Exit 0 ok; 1 refusals ("REFUSED <unit>[<index>]: <code>: <detail>"); 2 usage.
Deterministic: standard library only, no clock, no network, no LLM.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CORRECTABLE = ("required_by", "boundary_class")
ENTRY_KEYS = {"unit", "index", "quote", "field", "from", "to", "reason"}
SUFFIX = ".extract.json"


def canonical(items: list) -> bytes:
    return (json.dumps(items, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def load_json(path: Path, refusals: list[str], label: str):
    try:
        return json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        refusals.append(f"REFUSED {label}: unreadable: {exc}")
        return None


def compute(raw_dir: Path, corrections_path: Path, refusals: list[str]) -> dict[str, bytes]:
    units = sorted(p.name[: -len(SUFFIX)] for p in raw_dir.glob("*" + SUFFIX))
    if not units:
        refusals.append(f"REFUSED {raw_dir}: no_units: no *{SUFFIX} in the raw dir")
        return {}
    raw = {u: load_json(raw_dir / (u + SUFFIX), refusals, u) for u in units}
    doc = load_json(corrections_path, refusals, str(corrections_path))
    if refusals:
        return {}
    entries = doc.get("corrections") if isinstance(doc, dict) else None
    if not isinstance(entries, list):
        refusals.append(f"REFUSED {corrections_path}: corrections_invalid: expected {{\"corrections\": [...]}}")
        return {}
    items = {u: [dict(x) if isinstance(x, dict) else x for x in raw[u]] for u in units}
    seen: set[tuple[str, int, str]] = set()
    for n, entry in enumerate(entries):
        where = f"corrections[{n}]"
        if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
            refusals.append(f"REFUSED {where}: entry_invalid: keys must be exactly {sorted(ENTRY_KEYS)}")
            continue
        unit, index, field = entry["unit"], entry["index"], entry["field"]
        where = f"{unit}[{index}]"
        if unit not in items:
            refusals.append(f"REFUSED {where}: unknown_unit: no raw extraction {unit}{SUFFIX}")
            continue
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(items[unit]):
            refusals.append(f"REFUSED {where}: index_invalid: {index!r}")
            continue
        if field not in CORRECTABLE:
            refusals.append(f"REFUSED {where}: field_not_correctable: {field!r} (only {', '.join(CORRECTABLE)})")
            continue
        if not isinstance(entry["reason"], str) or not entry["reason"].strip():
            refusals.append(f"REFUSED {where}: reason_missing: every correction states its reason")
            continue
        key = (unit, index, field)
        if key in seen:
            refusals.append(f"REFUSED {where}: duplicate_correction: {field}")
            continue
        seen.add(key)
        item = raw[unit][index]
        if not isinstance(item, dict) or item.get("quote") != entry["quote"]:
            refusals.append(f"REFUSED {where}: quote_guard: the raw item's quote differs from the entry's")
            continue
        if item.get(field) != entry["from"]:
            refusals.append(f"REFUSED {where}: from_guard: raw {field} is {item.get(field)!r}, entry says {entry['from']!r}")
            continue
        if entry["to"] is None:
            items[unit][index].pop(field, None)
        else:
            items[unit][index][field] = entry["to"]
    return {u: canonical(items[u]) for u in units}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("apply", "check"):
        p = sub.add_parser(name)
        p.add_argument("--raw-dir", required=True)
        p.add_argument("--corrections", required=True)
        p.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    refusals: list[str] = []
    outputs = compute(Path(args.raw_dir), Path(args.corrections), refusals)
    out_dir = Path(args.out_dir)
    if not refusals and args.cmd == "check":
        for unit, data in outputs.items():
            path = out_dir / (unit + SUFFIX)
            if not path.is_file() or path.read_bytes() != data:
                refusals.append(f"REFUSED {unit}: output_drift: {path} != apply(raw, corrections)")
    if refusals:
        sys.stdout.write("".join(r + "\n" for r in refusals))
        sys.stdout.write(f"CORRECTIONS REFUSED: {len(refusals)} refusal(s)\n")
        return 1
    if args.cmd == "apply":
        out_dir.mkdir(parents=True, exist_ok=True)
        for unit, data in outputs.items():
            (out_dir / (unit + SUFFIX)).write_bytes(data)
    doc = json.loads(Path(args.corrections).read_text(encoding="utf-8"))
    counts = {}
    for entry in doc["corrections"]:
        counts[entry["unit"]] = counts.get(entry["unit"], 0) + 1
    tally = " ".join(f"{u}={counts.get(u, 0)}" for u in sorted(outputs))
    verb = "APPLIED" if args.cmd == "apply" else "CHECK OK"
    sys.stdout.write(f"CORRECTIONS {verb}: {len(outputs)} units; corrections {tally}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
