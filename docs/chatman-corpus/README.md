# The Chatman Corpus mdBook

This directory carries the receipted source capsule for **The Chatman Corpus**, a 317-target mdBook covering the James I. Chatman / Technology Applications Inc. historical record, Sean Chatman's LinkedIn publication lineage beginning with the 2022 Grandpa James reconstruction and 2024 IPOPrinter sequence, and the later Chatman Equation / authority / DfCM / ggen / receipt architecture.

## Canonical source capsule

`source/chatman-corpus-mdbook.tar.gz`

The archive expands to a normal mdBook project containing `book.toml`, `src/SUMMARY.md`, all referenced Markdown chapters, shared composed chapter material, and `CORPUS_RECEIPT.json`.

```bash
mkdir /tmp/chatman-corpus
cd /tmp/chatman-corpus
tar -xzf /path/to/chatman-corpus-mdbook.tar.gz
mdbook build docs/chatman-corpus
```

The repository's canonical-source-before-projection doctrine is preserved: Markdown is source; PDF/HTML are generated projections.

## Build standing

- Exact admitted repository base: `495cb16e91b2ac208043e19a432d3cc477ec77aa`
- mdBook chapter targets: `317`
- expanded rendered word count: `188,262`
- missing SUMMARY targets: `0`
- broken local Markdown links: `0`
- source capsule SHA-256: `b88b3b6d7cfa9578b8e123ccde1c9cf19d8b500a77459d04e93d04ae674a8b6f`
- local `mdbook` executable: `UNSUPPORTED` in the manufacturing environment
- PDF projection: generated from the exact `SUMMARY.md` order using the available HTML renderer; see `artifacts/chatman-corpus.pdf.sha256` for identity

## Evidence boundary

Historical James I. Chatman claims are separated from Sean Chatman's later reconstructions and synthetic TAI scenarios. Public LinkedIn indexing is incomplete, so the full article inventory is `PARTIAL_ALIVE`, not claimed complete. The 2030 material is a design horizon, not an observed future state.
