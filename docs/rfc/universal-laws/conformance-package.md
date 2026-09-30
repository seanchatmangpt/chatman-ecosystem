# Universal Laws — Executable Conformance Package

The RFC is implemented as one canonical package rather than independent prose and tests.

## Ownership

The canonical framework-neutral specification is `docs/rfc/universal-laws/v26.9.29-universal-laws.md`.

Machine-readable projections:

- `ontology/universal-laws/universal-laws.ttl` — vocabulary and UQ level graph.
- `ontology/universal-laws/universal-laws.shacl.ttl` — structural admission membrane.
- `schemas/universal-laws/conformance.schema.json` — portable conformance-claim envelope.
- `tests/universal-laws/vectors.json` — cross-runtime portable examples/counterexamples.
- `scripts/release_train/universal_laws_court.py` — dependency-free reference court.
- `tests/release_train/test_universal_laws_court.py` — repository-native focused court.

Generated or consumer-specific projections MUST cite this package rather than become parallel semantic owners.

## Reference execution

From repository root:

```bash
python3 scripts/release_train/universal_laws_court.py tests/universal-laws/vectors.json
python3 -m unittest tests.release_train.test_universal_laws_court -v
```

The portable court returns exit 0 only when every known vector reaches the expected classification. Unknown laws/cases remain typed UNKNOWN. The receipt always carries `authority=NONE`.

## Ecosystem validation

Repository doctrine remains authoritative for release validation:

```bash
python3 scripts/verify_release.py --check-refs
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Crown standing additionally requires the repository's Crown gate; merging this RFC does not itself claim Crown standing.

## Consumer rule

Consumers SHOULD import/reference the canonical vocabulary or project deterministic local representations. They MUST NOT copy the laws into a second authoritative ontology or allow a conformance result to acquire actuation authority.
