# playground/

Disposable, self-contained ggen project for validating
`ash-igniter-gen-pipeline-pack`'s ordering and gate behavior in isolation, without
touching the real `~/xaas` project.

## Usage

```bash
cd platform-console/services/ggen-marketplace/ggen-packs-src/ash-igniter-gen-pipeline-pack/playground
cp ../examples/02-full-chain.ttl ontology.ttl
ggen sync
```

Then inspect `.agp-receipts/*.mix.log` -- the file *modification order* (or, if `ggen sync`
prints its own per-row log, the printed order) should match ascending `agp:rank`: the
domain row first, then the resource, then the extend, then the migration.

The `sh_after mix ...` commands **will fail** here (no real Elixir/Ash/Igniter project
exists in `playground/`) -- that's expected. This harness validates ontology-to-command
generation and row ordering, not real Igniter side effects; real side effects are only
ever validated against `~/xaas` (see the pack's `MATURITY-MATRIX.md`).

`ontology.ttl`, `.agp-receipts/`, and ggen's own cache/state directories are gitignored --
swap in a different `examples/*.ttl` file and re-run freely; nothing here should ever need
a commit.
