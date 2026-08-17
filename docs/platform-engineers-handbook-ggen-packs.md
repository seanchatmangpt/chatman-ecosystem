# The Platform Engineer's Handbook — ggen Pack

> **Provenance record.** This document is the chatman-ecosystem-side completion record for a
> pack-conversion pass; the pack itself is canonical in `ggen-marketplace`, not here
> (`packs/` is authoritative source after admission per `ggen-marketplace/marketplace.toml`'s
> `[source_authority]`).

## What this is

The companion source code for Packt's *The Platform Engineer's Handbook* (Ajay Chankramath),
published at [`seanchatmangpt/Platform-Engineer-s-Handbook`](https://github.com/seanchatmangpt/Platform-Engineer-s-Handbook)
(upstream: `PacktPublishing/Platform-Engineer-s-Handbook`), captured as **one** `ggen-create`
pack — `platform-engineers-handbook` — admitted into `~/ggen-marketplace/packs/`.

## Why one pack, not fourteen

The source repository ships its 14 chapters as separate `ChNN/` directories, each a
chapter-scoped slice of the *same* evolving platform build (Ch01 lays the groundwork, Ch02
builds the cluster on top of it, and so on through Ch14). An earlier pass captured each
`ChNN/` as its own pack; that treated the book's own chapter split as if it were 14
independent projects, which it isn't — it's one project told incrementally.

This pack instead reconstructs the cumulative final-state project: chapters are layered in
book order (Ch01 → Ch14), each chapter's files copied over the accumulating tree at their
real project-relative path (the `ChNN/` prefix is stripped), so a same-path file from a
later chapter overwrites the earlier chapter's version — the way a real repo actually
evolves as it's built out. Three files collide across chapters this way and take their
final (Ch14 or latest-chapter) form: `README.md`, `load-secrets.sh`, `.circleci/config.yml`.

Result: 279 templated files (300 source files, minus 21 lost to those same-path chapter
overwrites, minus 1 excluded — see below).

## Pack

| Pack | Contents |
|---|---|
| `platform-engineers-handbook` | The complete, cumulative platform build across all 14 chapters, captured as one project |

Contains: `pack.toml` (marketplace manifest), `ggen.toml` (ggen-create project descriptor),
`ontology.ttl`, `templates/` (279 `.tmpl` files, content-hashed and numbered by
`ggen-create`), `ggen-create-package.json` (replacement manifest), `receipt.json`
(generation receipt).

Generated via the real `ggen-create` CLI session, run from the layered project tree:

```sh
ggen-create start platform-engineers-handbook
ggen-create add -r .
ggen-create remove templates/backend-service/v1/skeleton/.github/workflows/ci.yml
ggen-create usename PlatformEngineersHandbook
ggen-create generate --output ~/ggen-marketplace/packs
```

## Known exclusion

`templates/backend-service/v1/skeleton/.github/workflows/ci.yml` (originally
`Ch10/templates/backend-service/v1/skeleton/.github/workflows/ci.yml`) is itself a
Tera/Cookiecutter-style scaffold containing literal `{% raw %}...{% endraw %}` sentinels.
`ggen-create` fails closed on this (`TERA_RAW_SENTINEL_REFUSED`) rather than silently
corrupting the nested template syntax, so it was excluded from the captured file set before
`usename`/`generate`.

## Verification

Run through `ggen-create verify` against the real `ggen 26.8.8` binary (`ggen sync run`, not
a mock actuator):

```sh
ggen-create verify --output <dir> --ggen-bin "$(which ggen)" --set PlatformEngHandbook
```

Reconstruction and variation runs both exit `0` and write all 279 captured files;
checkpoints `P1_CAPTURE_PARITY` through `P6_REVISION_PARITY` are `ALIVE`; overall
`state: PARTIAL_ALIVE`. `P0_REFERENCE_IDENTITY` and `P7_PARITY_CROWN` sit at `UNEXECUTED`/
`PARTIAL_ALIVE` because no `--reference-dir` was supplied — there is no separate
upstream-generated "known good" render to diff against for this pack (unlike the
hygen-create greeter fixture, which has one). This is expected, not a failure.

## Marketplace qualification

Run through the real marketplace qualifier (`scripts/qualify_packs.py`), which loads every
admitted pack through `ggen` twice in an isolated filesystem-only capsule and requires
convergence to the same non-runtime consequence within a 5-second per-pass bound:

```sh
python3 scripts/qualify_packs.py --ggen "$(which ggen)" --report qualify-report.json
```

`platform-engineers-handbook` qualifies `ALIVE`: 563 consequence files, identical
`consequence_sha256` across both passes. (The one failure in the full 121-pack corpus run,
`clap-noun-verb-pack`, is a pre-existing `pack.toml` schema issue unrelated to this pack.)

## Known review finding (code vs. its own tests)

`test-platform-config.py` (Ch01) fails out of the box against the chapter's own shipped
`platform-config.yaml`, no modification needed: `test-platform-config.py:239` asserts
`"primary-cloud" in infra`, but `platform-config.yaml`'s `infrastructure:` section defines
`primary-runtime: "Kind"` — there is no `primary-cloud` key anywhere in the file. Real run:
`python3 test-platform-config.py` → `1 test(s) failed: Infrastructure: Missing
'primary-cloud'` (all other 9 checks pass). Either the test's key name or the config's key
name is wrong; they were never reconciled.

## Known review finding (book vs. code)

Spot-verification against the published PDF (*The Platform Engineer's Handbook*, Ajay
Chankramath, Packt, May 2026) surfaced one factual mismatch: the Preface and Chapter 3 TOC
state identity/access management uses OAuth via **Auth0**. The companion code implements
**Keycloak** throughout (`keycloak-realm-config.py`, `keycloak-oidc-module.ts`,
`keycloak-groups.py`; Ch03's own README says Keycloak explicitly). Zero references to Auth0
anywhere in the 300-file source repository.

## Scripts run for real

Beyond structural capture and `ggen sync run` fidelity, three independent, self-contained
scripts from three different chapters were actually executed against the merged project
(not just imported/linted):

- `design-principles-checklist.py platform-config.yaml` (Ch01) — real validation, all six
  design principles reported PASS.
- `test_templates.py::TestTemplateStructure` (Ch10, pytest) — 2/2 structural tests pass
  against the real `templates/backend-service/v1` Backstage scaffold.
- `friction-analyzer.py --workflow workflow.yaml` (Ch05) — real friction-score report:
  15 steps, 218 min serial / 150 min critical path, 31.2% parallelization potential.

Scripts requiring a live cluster or cloud credentials (`cost-analyzer.py`,
`platform-maturity-assessment.py`'s interactive mode, etc.) were not run — no infra was
faked or stubbed to force a pass.

Two more, using already-installed real tooling rather than mocks:

- `test-policies.py` (Ch11, offline default mode) — real `conftest` CLI (already installed
  at `/opt/homebrew/bin/conftest`) validates compliant/non-compliant Kubernetes manifests
  against the chapter's Rego policies: 6/6 tests pass.
- `test-ai-agents.py` (Ch14) — 15/15 tests pass: structural checks against the real
  `alert-correlator.py`, `incident-agent.py`, `rag-platform-docs.py`, and
  `runbook-automator.py` (role separation, safety-check presence, valid Python).

Four more offline-runnable chapter test suites, all pure `unittest` (no infra):

- `test-demo-app.py` (Ch05) — 7/7 pass.
- `test-onboarding.py` (Ch07) — 8/8 pass.
- `test-portal-health.py` (Ch06) — 7/7 pass.
- `test-rbac-permissions.py` (Ch03) — 9/9 pass.
- `test-platform-config.py` (Ch01) — 9/10 pass; the one failure is the real
  `primary-cloud`/`primary-runtime` key mismatch recorded below, not a false negative.

Nine chapters (01, 03, 05, 06, 07, 10, 11, 14, plus Ch05's friction-analyzer) now have at
least one real, independently-executed script or test suite run, not just imported.

## Not yet done

- Pack is not yet added to `ggen-marketplace/marketplace.toml`'s explicit catalog listing
  (packs are discovered by directory scan, so this doesn't block qualification, only
  catalog-page discoverability).
- No cluster-dependent chapter exercise has been run (would require a real Kind cluster,
  which this pass didn't stand up).

## See also

- [ggen as the Manufacturing Compiler](post-agi-platform-handbook/part-03-constructive-closure/12-ggen.md)
- [Appendix C — ggen Pack Anatomy](post-agi-platform-handbook/appendices/c-ggen-pack-anatomy.md)
