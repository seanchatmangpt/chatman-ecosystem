# QME-1 conformance

QME-1 qualification has four layers:

1. `schemas/qme-1/conformance.schema.json` validates record shape.
2. `conformance/qme-1/qme_conformance.py` applies semantic courts.
3. `tests/qme/test_qme_conformance.py` proves every semantic refusal has an executable killer fixture.
4. `fleet_reconcile.py` qualifies an exact, evidence-only fleet observation without promoting repository drift into authority.

The court is deliberately stdlib-only. It evaluates evidence and performs no authority grant or actuation.

## Core semantic refusals

The executable court covers exact subject, bounded consequence/value (MXinf), replay non-actuation, independent observation, anti-vacuity, observed violation, hidden semantics, authority promotion, generated-source provenance, negative-knowledge subject drift, Reverse-Chesterton guard retirement, external-authority promotion, negative-value promotion, canonical ownership and falsifier presence.

A negative court passes only when the attack is observed at the intended boundary and the forbidden outcome is not observed. A missing attack is `VACUOUS_COURT`, never success.

## Run

```bash
python3 conformance/qme-1/qme_conformance.py conformance/qme-1/fixtures/*.json
python3 -m unittest tests.qme.test_qme_conformance -v
python3 conformance/qme-1/fleet_reconcile.py conformance/qme-1/fleet-window-v26.9.30.json
python3 -m unittest tests.qme.test_fleet_reconcile -v
```

The fixture corpus is part of the conformance subject. Adding a semantic refusal without a killer fixture fails the unit test.

## Fleet reconciliation

`fleet-window-v26.9.30.json` freezes the exact Git subjects surfaced by the bounded seven-day fleet scan. Heads remain `OBSERVED`; the court refuses authority promotion, subject ambiguity, duplicate repositories, root substitution and capability sets that reference unobserved subjects. The fleet receipt is intentionally `PARTIAL_ALIVE` until stronger exact-head execution evidence exists.
