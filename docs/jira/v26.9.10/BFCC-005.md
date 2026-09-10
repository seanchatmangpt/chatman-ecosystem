# BFCC-005 — BFCC Doctrine Doc + Catalog Registration

Ticket Key: BFCC-005
Owning repo: seanchatmangpt/chatman-ecosystem
Exact base ref/SHA: main @ 83204ee38a518311d9c9fc128d69c517a99257f4
Standing: BFCC-CANDIDATE
Depends on: BFCC-002

## Problem

The full BFCC v1.0 doctrine (Prime Directive, ten gates, Regenerative Closure,
Compatibility definition, Receipt fields, Ultracode Execution Doctrine, Governing
Question) exists only as prose the user pasted into a conversation. It has no
canonical home in the repo and isn't registered in `catalog/documents.toml`, so
nothing else in the repo can cite it as a source of truth.

## Customer/system need

BFCC-003's verifier error messages, BFCC-007's case study, and any future subject
claiming BFCC compatibility need one authoritative doc to point to — the same role
`docs/FORMAL-DISCOVERY-FACTORY.md` and `docs/architecture/dfcm-public-ontology-profile.md`
play for their own catalogs.

## Scope

- `docs/BFCC.md` — the full doctrine, reformatted to this repo's markdown standards
  (H1 title matching filename, H2 sections, no line over 100 characters, code blocks
  fenced with a language, a See Also footer). Content: Prime Directive, the ten canon
  gates (C/A/D/S/G/Σ/E/T/W/I) each stated as Fuller principle → engineering projection
  → falsifier, Regenerative Closure, the Boolean-compatibility definition, the receipt
  field list (matching BFCC-002's `[receipt].required_fields` exactly — no drift
  between the doc and the machine-readable manifest), and the Ultracode Execution
  Doctrine (CANON → INVENTORY → MAP → DFCM → TRIMTAB → IMPLEMENT → FALSIFY →
  EPHEMERALIZATION AUDIT → RECEIPT).
- `catalog/documents.toml`: one new `[[document]]` entry —
  `id = "document:bfcc"`, `title = "BFCC — Buckminster Fuller Canon Compatibility"`,
  `path = "docs/BFCC.md"`, `canonical = false` (matches the sibling doctrine docs'
  pattern — `formal-discovery-factory` and `frontier-release-factory` are also
  `canonical = false`).

## Non-goals

- No claim that any subject in the repo is BFCC-compatible — this ticket is
  documentation + registration only.
- No re-litigation of the doctrine's content — this ticket transcribes and reformats
  what the user already specified, it does not redesign the canon.

## Dependencies

BFCC-002 (the receipt field list this doc's Receipt section must match verbatim).

## Risks

Doc/manifest drift if `catalog/bfcc.toml`'s `[receipt].required_fields` changes later
without updating `docs/BFCC.md` to match — mitigate by treating the manifest as the
source of truth and the doc as generated prose from it in any future edit, per this
repo's "link to the most authoritative version" markdown rule.

## Authority boundary

Pure documentation. No DO authority implied or claimed.

## Rollback

Delete `docs/BFCC.md` and revert the `catalog/documents.toml` entry; no script
references either yet.

## Acceptance commands

```
python3 -c "import tomllib; d = tomllib.load(open('catalog/documents.toml','rb')); assert any(e['id']=='document:bfcc' for e in d['document']); print('registered OK')"
python3 -c "import pathlib; p = pathlib.Path('docs/BFCC.md'); assert p.exists(); lines = p.read_text().splitlines(); over = [l for l in lines if len(l) > 100 and not l.strip().startswith('|')]; print('over-100-char non-table lines:', len(over))"
```

## Observable Definition of Done

- `docs/BFCC.md` exists, has exactly one H1, uses H2 for major sections, no bare
  over-100-character lines outside tables/code blocks.
- `catalog/documents.toml` has the new entry and still parses as valid TOML with the
  same total entry count plus one.
- The Receipt section's field list matches `catalog/bfcc.toml`'s
  `[receipt].required_fields` exactly, field-for-field.
