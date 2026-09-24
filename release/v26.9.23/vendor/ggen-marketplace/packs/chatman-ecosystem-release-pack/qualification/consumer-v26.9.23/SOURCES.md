# consumer-v26.9.23 sources

Runnable consumer of this pack for the Chatman Ecosystem v26.9.23 role crosswalk (CE23-1,
CE23-2). Every file under `imports/` is either a byte copy of a committed source or a
deterministic lift of one. `release.ttl` is qualification data: the two component SHAs are
real pushed heads, and the role names and constitutional mappings are fixture choices, not
v26.9.23 release decisions (those belong to chatman-ecosystem `release/v26.9.23`).

## Inputs

| file | source | sha256 |
|---|---|---|
| `imports/manifest-v26.9.1.toml` | `git show c59596f5506e7a00ca4ed6b909ebf6d6659b74c1:release/v26.9.1/manifest.toml` in a clone of seanchatmangpt/chatman-ecosystem (GitHub main at CE23-0) | `30b1d83ce544299557da50084ced696172d219f6790c2cfc5b78116902850949` |
| `imports/legacy-v26.9.1.ttl` | `python3 ../../lift/manifest_to_er.py imports/manifest-v26.9.1.toml https://github.com/seanchatmangpt/chatman-ecosystem/release/v26.9.1 "seanchatmangpt/chatman-ecosystem@c59596f5506e7a00ca4ed6b909ebf6d6659b74c1:release/v26.9.1/manifest.toml"` | `683a1cef30086c88453d73a0b9eb4b3c1f5a0fdfb17004a92e4e7842ec183170` |
| `imports/fleet-classification.ttl` | `git show b4ef5d664cb5afa2ab5456ac20d28500f5b00144:docs/sjira/v26.9.23/fleet/classification.ttl` in seanchatmangpt/xaas (on origin/friday/gc-fri-0800; blob 7d7bd287, unchanged at the int head 8a54c93d) | `d9e99f074ef2a8c994119681d9359ea1778e68333cc8da94b6b1c0aa44873636` |
| `imports/court-references.ttl` | observation, see below | recorded in the receipt |
| `imports/ce23-orders.ttl` | `git show 35b3ed073dbc3785b7931eea7ba3c8d657a4b4e3:release/v26.9.23/sjira/compiled/chatman-ce23/orders.ttl` (chatman-ecosystem lane branch ce23/CE-INTAKE; 21 WorkOrders compiled from chatman-ce23.md) | `01cd0ae2d743a3be370b4e7cd719be6d684cc81db3e2626cfa3bcd4e693963a2` |

The lift reproduces byte-identically: running the command above again gives the same sha256.

## Court-reference observation

`fleet_matrix.court_references(courts_dir, {"name": n, "path": "/Users/sac/" + n})` from
`scripts/sjira/fleet_matrix.py` at xaas b4ef5d66, run read-only over the 16 court scripts
`docs/sjira/v26.9.23/courts/*.sh` extracted from that commit, for the 16 v26.9.1 component
repositories plus xaas and ggen_igniter. Output:

- every one of the 16 v26.9.1 repositories: `[]`
- xaas: GC23-0, GC23-1, GC23-10, GC23-11, GC23-2, GC23-3, GC23-4, GC23-5, GC23-6, GC23-7,
  GC23-8, GC23-9
- ggen_igniter: GC23-0, GC23-1, GC23-10, GC23-11, GC23-2, GC23-3, GC23-5, GC23-6, GC23-8,
  GC23-9, gi_mix

`imports/court-references.ttl` states exactly these hits as `er:courtReferencesComponent`
facts with the `owner/name` slug as object.

## Release court and root receipt (pack 0.4.0)

`release.ttl` also declares a court for this consumer (qualification data): three gates (the
explicit runner over this graph, `shasum -a 256 -c --strict out/receipts/IMPORTS.sha256`, and a
consumer-owned check that the rendered crosswalk disposes 16 roles), five probes (`git rev-parse
HEAD` as the receipt subject, `ggen --version`, `python3 --version`, sha256 of the pack
`ontology.ttl` and of `release.ttl`), one typed check and three imports:

- typed check `Dependency license and source policy`: `gh api
  repos/seanchatmangpt/chatman-ecosystem/commits/c59596f5506e7a00ca4ed6b909ebf6d6659b74c1/check-runs`
  (2026-09-23) lists check-run 103106030500 with conclusion `failure` (Crown Admission,
  `.github/workflows/crown.yml`, run 34548430864, push); `gh api .../actions/jobs/103106030500`
  names the failing step `Run cargo deny check`. Typed `pre_existing`, boundary SUCCESSOR.
- imports: the three byte copies of the table above (`manifest-v26.9.1`, `fleet-classification`,
  `ce23-orders`), with the sha256 values listed there.

`observed.ttl` is the court's own output, never hand-written: at the lane commit named by its
`subject_sha` line, in this directory, with `observed.ttl` holding only its prefix line, `ggen sync
run` then `COURT_OBSERVED=observed.ttl bash out/scripts/crown_v26_9_23.sh` (exit 0, `COURT_ALIVE`).
Its last statement is the release's `er:observedCourtInput` set (14 elements: the court, 2
components, 3 imports, 5 probes, 3 gates); gate 095 refuses it once any of those inputs is edited,
so changing a gate, probe, import, component SHA or the court root here means re-running the court.
It is committed in the child commit, since a commit cannot contain its own SHA. `qualification/qualify.sh` step 7 re-runs the court in a git copy
of the pack and requires every line except the subject line to reproduce; the subject must be an
ancestor of HEAD.

## Expected consequence

`ggen sync run` (ggen 26.9.18) exits 0 and writes the crosswalk files under `out/` (not committed): the
five in-universe roles (public-ontology, manufacture, pack-marketplace, actuation, explore) are
SUCCESSOR by `rule:fleet-classification`, the other eleven are SUCCESSOR by
`rule:no-GC23-court-reference`, and no role is REQUIRED. A second run skips every file as
identical.

The same sync also writes the 0.4.0 outputs: `out/scripts/crown_v26_9_23.sh`,
`out/typed-checks.txt` (one line), `out/receipts/IMPORTS.sha256` (three lines), and, from the
committed observation, `out/receipts/root-receipt.unsealed.toml` (PARTIAL_ALIVE -> ALIVE, subject =
the observed commit) and `out/receipts/ROOT.json` (ADMITTED by `~/.claude/dfcm/validate_receipt.py`).
With `observed.ttl` holding only its prefix line (before the court), both receipts are still
written, typed: subject `UNOBSERVED`, PARTIAL_ALIVE -> PARTIAL_ALIVE, ROOT.json `broken_term`
`R_missing_identity` (refused by the fleet validator). The court removes both when it writes its
observation, so the following sync renders them from it.
