# QME-1 conformance

QME-1 qualification has three layers:

1. `schemas/qme-1/conformance.schema.json` validates record shape.
2. `conformance/qme-1/qme_conformance.py` applies semantic courts.
3. `tests/qme/test_qme_conformance.py` proves every semantic refusal has an executable killer fixture.

The court is deliberately stdlib-only. It evaluates evidence and performs no authority grant or actuation.

## Core semantic refusals

The executable court covers exact subject, bounded consequence/value (MXinf), replay non-actuation, independent observation, anti-vacuity, observed violation, hidden semantics, authority promotion, generated-source provenance, negative-knowledge subject drift, Reverse-Chesterton guard retirement, external-authority promotion, negative-value promotion, canonical ownership and falsifier presence.

A negative court passes only when the attack is observed at the intended boundary and the forbidden outcome is not observed. A missing attack is `VACUOUS_COURT`, never success.

## Run

```bash
python3 conformance/qme-1/qme_conformance.py conformance/qme-1/fixtures/*.json
python3 -m unittest tests.qme.test_qme_conformance -v
```

The fixture corpus is part of the conformance subject. Adding a semantic refusal without a killer fixture fails the unit test.
