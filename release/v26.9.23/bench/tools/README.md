# CE23-12 bench draft tools

These are the draft qualification that `../DESIGN.md` cites (§15, §395-410). Both came from the retired
driver's scratch directory `BENCH-design/tools/` on 2026-09-24. They now resolve paths relative to
this file, never through a shadow checkout.

- `verify_draft.py` runs the SHACL and mutation checks over `../ontology-draft.ttl` and
  `../candidates/*.ttl`. Run: `python3 release/v26.9.23/bench/tools/verify_draft.py` (exit 0, ALL CHECKS PASS).
- `mk_extract.py` rebuilds `../candidates/*.extract.json` from `../../sjira/chatman-ce23-12-{bench,standings}.md`.
  A rerun is byte-identical to the committed candidates (empty `git diff`).
- `prose_spans.py` is owned by xaas `scripts/sjira/prose_spans.py` (sha256 86a0e9b3...) and is not copied here.
