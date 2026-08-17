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

## Not yet done

- Pack is not yet added to `ggen-marketplace/marketplace.toml`'s catalog entries or
  qualification gates. Capture and single-binary verify only; not yet published/qualified
  by the marketplace's own qualifier.

## See also

- [ggen as the Manufacturing Compiler](post-agi-platform-handbook/part-03-constructive-closure/12-ggen.md)
- [Appendix C — ggen Pack Anatomy](post-agi-platform-handbook/appendices/c-ggen-pack-anatomy.md)
