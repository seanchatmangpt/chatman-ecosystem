# OCEL Process Evidence — v26.8.18

## Standing

`PARTIAL_ALIVE`

OCEL accumulation and live status are observed. Durable storage and the wasm4pm-backed discovery edge are not closed.

## Current path

```text
real mesh traffic
  -> Envoy / OTLP spans
  -> OTel Collector
  -> OCEL accumulator
       -> otel_span_to_ocel_evidence(...)
       -> deduplicated append-only JSONL
       -> canonical OCEL v2 JSON
       -> /status
       -> /discovery  [incomplete / fail-closed]
  -> platform-console /ocel-log
```

The accumulator is not a parallel synthetic benchmark stream. It receives one of the Collector's real fan-out streams from the same observed platform traffic used by Jaeger and standing-weaver.

## Observed execution

The admitted descendant implementation commit for this documentation release records live gateway traffic causing accumulator state to grow:

- events: `24 -> 29`
- objects: `14 -> 17`

A proxy port defect was found during verification: the client defaulted to port `8090` while the real Kubernetes Service uses `4900`. The implementation was corrected before the capability was documented as reachable.

This is stronger than manifest existence: the accumulator's changing event/object state was observed under real traffic.

## Object-centric role

OCEL provides a process-state representation complementary to receipts:

- **receipt:** proves identity/authority/consequence/replay obligations for an admitted operation;
- **OCEL event/object graph:** represents what happened to which objects and in what relationships/order.

Neither replaces the other. A process event is not an actuation receipt; a receipt need not encode the entire process-mining graph.

## Admission boundary

Raw OTLP input is observation, not canonical process truth. The transformer constructs bounded OCEL evidence from admitted telemetry semantics. Future enrichment must preserve provenance back to the originating span/request/subject rather than allowing inferred process structure to masquerade as directly observed state.

## `/ocel-log`

The platform-console surface is viewer-gated and polls the accumulator through a server-side proxy. The UI must preserve the backend's actual state:

- `/status` success -> show real counts/timestamp;
- backend unavailable -> explicit error;
- `/discovery` unavailable -> explicit error;
- no hard-coded fallback counts or invented discovery graph.

## `/discovery`

The intended next edge is a real subprocess bridge to `wasm4pm-cli` over the accumulator's current OCEL log. At the v26.8.18 reviewed baseline this edge is **not complete**.

Correct standing is therefore:

```text
accumulation: ALIVE for observed local subject
status query: ALIVE for observed local subject
discovery: PARTIAL_ALIVE / incomplete edge
durable OCEL service: PARTIAL_ALIVE
aggregate OCEL process-evidence rail: PARTIAL_ALIVE
```

A sparse or trivial discovery result over real operational telemetry is valid. Fabricating a richer model to make the demo look complete is not.

## Persistence

The accumulator currently uses `emptyDir`. That means pod restart can destroy accumulated process evidence. This is acceptable for the bounded local v26.8.18 experiment only when disclosed; it is not sufficient for a production process ledger or long-lived standing evidence.

Durability closure requires an explicitly verified persistent store plus replay/recovery evidence.

## Replay target

A closed replay experiment should bind:

1. exact source telemetry set or deterministic capture;
2. transformer identity/version;
3. OCEL output digest;
4. event/object counts and object identifiers;
5. discovery executable/toolchain identity;
6. discovery output digest or typed refusal;
7. repeated execution comparison.

## Security

OTLP/OCEL data is untrusted observation until admitted. It must not:

- inject shell arguments into discovery execution;
- select arbitrary executables;
- acquire Kubernetes or filesystem authority from event attributes;
- overwrite canonical evidence without a brokered mutation/receipt path.

The discovery bridge should use an argument-safe subprocess boundary and explicit input/output locations, with bounded time/resource limits.

## Closure work

1. complete and execute the real wasm4pm `/discovery` bridge;
2. add negative fixtures for malformed/hostile OCEL input;
3. move standing-relevant OCEL state from `emptyDir` to verified durable storage;
4. add deterministic replay/digest comparison;
5. connect resulting process evidence to receipt/provenance identity without collapsing the two types;
6. promote standing only after exact-head execution of those edges.

## Falsifiers

OCEL standing must fall if event counts are synthetic, the accumulator is disconnected from real Collector traffic, `/discovery` fabricates data on failure, a restart loses data after durability is claimed, or an event-derived intent actuates without BRCE and an actuation receipt.
