# Chateco PhD Book Source

This directory is the standalone mdBook source for **The Chateco Research Program**. It is intentionally additive to the existing root documentation book.

## Subject

- repository: `seanchatmangpt/chatman-ecosystem`
- frozen base: `495cb16e91b2ac208043e19a432d3cc477ec77aa`
- source corpus digest (SHA-256): see `manifest.json`
- manuscript: 141 numbered chapters + 26 appendices

## Canonical publication source

For this edition, `src/**/*.md` is the authored publication source. `book/` is a disposable mdBook projection and is not committed. `manifest.json` records the bounded source relationship used to manufacture this edition; it does not confer standing on referenced repositories.

## Verify

```bash
python3 verify.py
mdbook build
```

The Python verifier proves only structural invariants (all SUMMARY targets exist, chapter/appendix cardinality, and minimum chapter substance). The mdBook build is a separate execution obligation.

## Standing

Local structural verification and parser validation establish a candidate manuscript, not ecosystem `ALIVE`. Exact-head CI must execute the pinned mdBook build before publication standing can advance. Research claims remain bounded by the evidence stated inside the chapters.
