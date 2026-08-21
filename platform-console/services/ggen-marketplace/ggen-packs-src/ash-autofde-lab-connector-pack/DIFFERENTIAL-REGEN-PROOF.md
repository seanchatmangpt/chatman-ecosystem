# Differential Regeneration Proof — ash-autofde-lab-connector-pack

Real evidence that `ggen sync run --dry-run` regenerates only the file(s)
affected by an ontology change and reports every other file's output as
unchanged/skipped, rather than re-rendering the whole pack on every run.

Binary used: `~/chatman-ecosystem/platform-console/services/ggen/ggen-src/target/debug/ggen`
(built from the `ggen-cli-lib` crate, `cargo +nightly-2026-06-22`).
Command run from this pack's own directory (relative `lib/xaas/...` output
paths resolve under the pack dir, never touching the real `~/xaas` checkout).

## 1. Baseline — before

At the time of this run, `ontology.ttl` already carried 3
`aac:AshConnector` individuals from concurrent work (`AutofdePlannerCandidate`,
`AutofdePlannerCatalog`, `AutofdePlannerMatch`). No prior dry-run had been
executed in this pack directory, so no local `lib/` output existed yet:

```json
{
  "written": [
    "lib/xaas/operations/autofde_planner_candidate.ex",
    "lib/xaas/operations/autofde_planner_catalog.ex",
    "lib/xaas/operations/autofde_planner_match.ex"
  ],
  "skipped": [],
  "graph_hash_hex": "6f280f63ca09147db39c9d6371b78480197e3463cbc06b6f5923f82d51f1fb94",
  "decisions": {
    "lib/xaas/operations/autofde_planner_candidate.ex": "planned: write (dry-run)",
    "lib/xaas/operations/autofde_planner_catalog.ex": "planned: write (dry-run)",
    "lib/xaas/operations/autofde_planner_match.ex": "planned: write (dry-run)"
  },
  "closure": {
    "ontology.ttl": "d5e95651c3372cc678cd448a025aee293507213f26a6ef11a62e4f8a422f4d29",
    ...
  }
}
```

Observed behavior worth noting: `--dry-run` in this ggen build still
materializes the target files on disk (they did not previously exist under
the pack's local `lib/`), which is what makes the second run's
content-comparison possible. It does not touch `~/xaas` — the paths are
relative to the pack's own working directory.

## 2. Test edit

Added one new individual, `aac:AutofdePlannerStatus`, to `ontology.ttl` —
purely additive, no existing individual's triples were touched:

```turtle
aac:AutofdePlannerStatus a aac:AshConnector ;
  dcterms:description "DIFFERENTIAL-REGEN-TEST individual (reverted after proof capture): ..." ;
  aac:resourceModule "Xaas.Operations.AutofdePlannerStatus" ;
  aac:domainModule "Xaas.Operations" ;
  aac:invokeTool "fabric__status" ;
  aac:actionName "request_status" ;
  aac:cnvDeployBaseUrlEnv "cnv_deploy_base_url" ;
  aac:outputFile "lib/xaas/operations/autofde_planner_status.ex" ;
  aac:tableName "autofde_planner_status_requests" .
```

## 3. After — second dry-run

```json
{
  "written": [
    "lib/xaas/operations/autofde_planner_status.ex"
  ],
  "skipped": [
    ["lib/xaas/operations/autofde_planner_candidate.ex", "unchanged: content identical"],
    ["lib/xaas/operations/autofde_planner_catalog.ex", "unchanged: content identical"],
    ["lib/xaas/operations/autofde_planner_match.ex", "unchanged: content identical"]
  ],
  "graph_hash_hex": "3844c0b3233b288a27861bf5297807a9b9ba786a838627e7e6eb68ecd8045f9f",
  "decisions": {
    "lib/xaas/operations/autofde_planner_candidate.ex": "skipped: unchanged: content identical",
    "lib/xaas/operations/autofde_planner_catalog.ex": "skipped: unchanged: content identical",
    "lib/xaas/operations/autofde_planner_match.ex": "skipped: unchanged: content identical",
    "lib/xaas/operations/autofde_planner_status.ex": "planned: write (dry-run)"
  },
  "closure": {
    "ontology.ttl": "dd099c17742695494001c33a217d34c253b7eb971981273c4245e1b80322d042",
    ...
  }
}
```

## 4. The real diff

| File                                          | Run 1 (baseline)         | Run 2 (after +1 individual) |
|------------------------------------------------|---------------------------|------------------------------|
| `autofde_planner_candidate.ex`                 | written (first creation)  | **skipped: unchanged**       |
| `autofde_planner_catalog.ex`                   | written (first creation)  | **skipped: unchanged**       |
| `autofde_planner_match.ex`                     | written (first creation)  | **skipped: unchanged**       |
| `autofde_planner_status.ex` (new individual)   | did not exist              | **written**                  |

Adding exactly one new individual regenerated exactly one new output file.
The three pre-existing outputs, whose source individuals were not touched,
were content-hashed against their already-materialized files and reported
`skipped: unchanged: content identical` — proving the pipeline diffs at the
individual/output-file level, not a blanket re-render of the whole pack.
`graph_hash_hex` and the `ontology.ttl` closure hash both changed between
runs (reflecting the real ontology edit); `templates/ash_connector_resource.tmpl`'s
closure hash and every other unaffected closure entry stayed identical.

## 5. Cleanup (verified, not asserted)

- `aac:AutofdePlannerStatus` was removed from `ontology.ttl` immediately
  after capturing the run-2 output. `git diff ontology.ttl` after the
  revert shows only the pre-existing concurrent-work addition of
  `AutofdePlannerMatch` (present before this test started) — the test
  individual leaves zero trace.
- The locally-materialized `lib/` directory created by the dry-runs (a
  side effect of this ggen build's `--dry-run`, confined to this pack's
  own working directory) was deleted (`rm -rf lib`) so this test leaves
  no other on-disk residue.
- Nothing under `~/xaas` or `~/autofde-lab` was read or written by this
  proof.
