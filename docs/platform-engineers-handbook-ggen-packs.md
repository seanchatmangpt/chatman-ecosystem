# The Platform Engineer's Handbook — ggen Packs

> **Provenance record.** This document is the chatman-ecosystem-side completion record for a
> pack-conversion pass; the packs themselves are canonical in `ggen-marketplace`, not here
> (`packs/` is authoritative source after admission per `ggen-marketplace/marketplace.toml`'s
> `[source_authority]`).

## What this is

The companion source code for Packt's *The Platform Engineer's Handbook* (Ajay Chankramath),
published at [`seanchatmangpt/Platform-Engineer-s-Handbook`](https://github.com/seanchatmangpt/Platform-Engineer-s-Handbook)
(upstream: `PacktPublishing/Platform-Engineer-s-Handbook`), converted chapter-by-chapter into
14 `ggen-create` packs and admitted into `~/ggen-marketplace/packs/`.

Each chapter (`ChNN/` in the source repo) became one pack, generated with the real
`ggen-create` CLI end-to-end session:

```sh
ggen-create start platform-eng-chNN
ggen-create add -r .
ggen-create usename PlatformEngineersHandbook
ggen-create generate --output ~/ggen-marketplace/packs
```

## Pack index

| Pack | Chapter | Topic |
|---|---|---|
| `platform-eng-ch01` | 1 | Laying the Groundwork |
| `platform-eng-ch02` | 2 | Building the Cluster Foundation |
| `platform-eng-ch03` | 3 | Identity, Access, and Policy Guardrails |
| `platform-eng-ch04` | 4 | Observability from Day One |
| `platform-eng-ch05` | 5 | Developer Experience and Golden Paths |
| `platform-eng-ch06` | 6 | The Developer Portal (Backstage) |
| `platform-eng-ch07` | 7 | Self-Service Onboarding |
| `platform-eng-ch08` | 8 | Progressive Delivery Pipelines |
| `platform-eng-ch09` | 9 | Self-Service Infrastructure (Crossplane) |
| `platform-eng-ch10` | 10 | Starter Kits and Templates |
| `platform-eng-ch11` | 11 | Policy as Code and Compliance |
| `platform-eng-ch12` | 12 | Cost Optimization (FinOps) |
| `platform-eng-ch13` | 13 | Resilience, Backup, and Disaster Recovery |
| `platform-eng-ch14` | 14 | AI-Augmented Platform Engineering |

Each pack directory contains: `pack.toml` (marketplace manifest), `ggen.toml` (ggen-create
project descriptor), `ontology.ttl`, `templates/` (one `.tmpl` per captured file, content
hashed and numbered by `ggen-create`), `ggen-create-package.json` (replacement manifest),
and `receipt.json` (generation receipt).

## Known deviation: Ch10

`Ch10/templates/backend-service/v1/skeleton/.github/workflows/ci.yml` is itself a
Tera/Cookiecutter-style scaffold containing literal `{% raw %}...{% endraw %}` sentinels.
`ggen-create` fails closed on this (`TERA_RAW_SENTINEL_REFUSED`) rather than silently
corrupting the nested template syntax. That one file was excluded from the pack's captured
file set (`ggen-create remove <path>`) before `usename`/`generate`; the rest of Ch10's 36
templates captured normally.

## Not yet done

- No `Appendix A` directory exists in the source repository at the cloned ref — only
  `Ch01`–`Ch14` — so no corresponding pack was created for it.
- Packs have not yet been run through `ggen-create verify` / `ggen-create package verify`
  against a real `ggen` render, nor added to `ggen-marketplace/marketplace.toml`'s catalog
  entries or qualification gates. Structural capture only; not yet qualified.

## See also

- [ggen as the Manufacturing Compiler](post-agi-platform-handbook/part-03-constructive-closure/12-ggen.md)
- [Appendix C — ggen Pack Anatomy](post-agi-platform-handbook/appendices/c-ggen-pack-anatomy.md)
