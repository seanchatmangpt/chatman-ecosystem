# QME-1 conformance

QME-1 qualification has four layers:

1. `schemas/qme-1/conformance.schema.json` validates record shape.
2. `conformance/qme-1/qme_conformance.py` applies semantic courts.
3. `tests/qme/test_qme_conformance.py` proves every semantic refusal has an executable killer fixture.
4. `qme_fleet_projection.py` composes QME over the canonical 101-repository fleet observation from PR #310 without creating another observer.

The court is deliberately stdlib-only. It evaluates evidence and performs no authority grant or actuation.

## Core semantic refusals

The executable court covers exact subject, bounded consequence/value (MXinf), replay non-actuation, independent observation, anti-vacuity, observed violation, hidden semantics, authority promotion, generated-source provenance, negative-knowledge subject drift, Reverse-Chesterton guard retirement, external-authority promotion, negative-value promotion, canonical ownership and falsifier presence.

A negative court passes only when the attack is observed at the intended boundary and the forbidden outcome is not observed. A missing attack is `VACUOUS_COURT`, never success.

## Run

```bash
python3 conformance/qme-1/qme_conformance.py conformance/qme-1/fixtures/*.json
python3 -m unittest tests.qme.test_qme_conformance -v
python3 scripts/release_train/fleet_recent_activity_court.py observations/fleet/2026-09-30-seven-day.json
python3 conformance/qme-1/qme_fleet_projection.py observations/fleet/2026-09-30-seven-day.json conformance/qme-1/fleet-projection-v26.9.30.json
python3 -m unittest tests.qme.test_qme_fleet_projection -v
```

The fixture corpus is part of the conformance subject. Adding a semantic refusal without a killer fixture fails the unit test.

## Fleet composition

The fleet observer owns current Git-state observation. QME consumes its exact observation as candidate evidence; it does not rescan GitHub or duplicate its schema. The projection remains `PARTIAL_ALIVE`, `authority=NONE`, and refuses any observed capability that is absent from the canonical 101-repository source.
