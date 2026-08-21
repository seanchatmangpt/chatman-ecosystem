# examples/

Standalone ontology fact fixtures for `ash-igniter-gen-pipeline-pack`. These are ontology
fact fixtures only -- no `mix` command is expected to succeed against them outside a real
Ash/Igniter project. Their purpose is proving SPARQL row ordering (`agp:rank`) and gate
correctness, not real Igniter execution.

Use with `../playground/` (see its README) to run a real `ggen sync` and inspect the
rendered `sh_after` command order in `.agp-receipts/*.mix.log`.

| File | Demonstrates |
|---|---|
| `01-single-domain-resource.ttl` | Smallest ordered case: one rank-0 domain, one rank-1 resource depending on it. |
| `02-full-chain.ttl` | Full real chain: rank 0 domain -> rank 1 resource -> rank 2 extend -> rank 3 migration. |
| `03-fan-out.ttl` | One rank-0 domain, 5 rank-1 resources depending on it -- fan-out and ordering together. |
