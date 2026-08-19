# otel-weaver-ocel-pack -- STATUS: source missing, real gap

`weaver-wrapper.sh` in this directory is a real, verified-working copy of
`/Users/sac/chicago-tdd-tools/weaver-toolkit/weaver-wrapper.sh` (186 lines,
bash), ported here per the 80/20 fix pass on 2026-08-19 rather than
reinvented. It wraps the real upstream `open-telemetry/weaver` CLI
(`bootstrap`/`check`/`live-start`/`live-stop`/`version` subcommands) and was
independently verified in chicago-tdd-tools: `check` passed real static
validation against a real semantic-convention registry, and
`live-start`/`live-stop` spawned and cleanly killed a real
`registry live-check --otlp-grpc-port ... --admin-port ...` subprocess,
writing a real `report.json`. Env-var configurable: `WEAVER_VERSION`,
`WEAVER_HOME`, `WEAVER_REGISTRY_PATH`, `WEAVER_OTLP_GRPC_PORT`,
`WEAVER_ADMIN_PORT`, `WEAVER_REPORTS_DIR`. See
`~/chicago-tdd-tools/weaver-toolkit/README.md` for the full verify-python
Chicago-style test suite (6/6 real passing tests) that certifies it.

## What is NOT here (named, confirmed gap, not silently patched around)

This pack's actual generated source --
`generated/src/bin/ocel_accumulator.rs` and the `otel_span_to_ocel_evidence`
transformer it's supposed to call -- do not exist anywhere in this
`chatman-ecosystem` checkout. Confirmed by exhaustive search over the whole
tree (every ggen pack directory, every `*.rs` file) on 2026-08-19: zero
matches for either name outside of comments in `k8s/ocel-accumulator.yaml`
and `app/lib/ocel-log.ts` that cite this path.

The `ocel-accumulator` Deployment in `istio-system` is running a real,
already-built binary (image `ocel-accumulator:local`) that was compiled and
loaded into the kind cluster's node image cache from a location or branch
not present in this checkout. That binary has one confirmed real bug: its
`/status` endpoint always serializes `lastUpdated: null` even though real
events exist on disk with a real write timestamp -- the timestamp is never
threaded from the event-append path into the status struct. This cannot be
fixed in source here without first recovering or fully re-authoring the
missing pack (a full OTLP-JSON -> OCEL transformer plus dedup logic), which
was judged out of scope for this pass rather than risk silently
reimplementing dedup/mapping semantics that don't match the lost original
and calling it a "fix."

Recovering the real source (git history on another branch/machine, a CI
artifact, or the original author's local checkout) is the correct next step
before attempting the `lastUpdated` fix in code.
