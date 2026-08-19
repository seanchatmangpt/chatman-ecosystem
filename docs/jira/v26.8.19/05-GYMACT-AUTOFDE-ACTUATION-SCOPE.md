# gymact / autofde-lab Actuation Scope for v26.8.19

## Backward from finished, then corrected against real source

The premise "we can simulate time passing in gymact" and "use gymact/autofde-lab to actuate all
remaining work" is worth taking seriously rather than dismissing — but taking it seriously means
checking gymact's and autofde-lab's real source before writing the rest of this ticket set, not
after. This ticket is that check, done first, so every claim in `01`-`04` about what these tools
can and cannot do is grounded, not asserted.

## What gymact actually is, checked against `~/gymact/src/gymact/`

- **No time-simulation capability.** `kernel.py`'s `RuntimeLimits` defines real wall-clock
  timeouts on real operations (`materialize_timeout_s`, `observe_timeout_s`,
  `actuate_timeout_s`, `verify_timeout_s`, `teardown_timeout_s`, `recovery_timeout_s`,
  `authority_timeout_s`) — these bound how long gymact will wait for a real action to complete,
  not a mechanism for compressing or fast-forwarding an external clock (AWS's review queue,
  GCP's partner-status approval, a human signing an EULA). Checked via `grep -n
  "time\|Time\|duration\|Duration\|simulate\|Simulate" kernel.py` — every match is a real
  timeout constant, nothing resembling simulated elapsed time.
- **Real, narrow, checked actuation surface for platform-console today.** The only registered
  provider (`src/gymact/gyms/platform_console_provider.py`) exposes exactly two capabilities:
  - `run_inventory_components` (DO) — `POST /api/castle/run` with a fixed, non-caller-supplied
    verb id.
  - `get_castle_jobs` (READ) — `GET /api/castle`.
  Both were exercised for real, live, in this session's prior turn: a freshly-minted API key,
  a real `materialize → observe → actuate → verify → teardown` cycle, `POST /api/castle/run`
  returning `201`, a real k8s `Job` reaching `Complete` in 3 seconds, the key revoked and a real
  `401` confirmed afterward.
- **What `run_inventory_components` actually runs.** `app/lib/castle.ts`'s
  `ALLOWED_CASTLE_VERBS` is a closed set — `fortune5-requirements`, `inventory-components`,
  `inventory-goals` — each a real, already-shipped, side-effect-free castle CLI subcommand.
  There is no verb in this allowlist, and no code path in `castle.ts`, that could construct
  a `castle construct` or any mutating invocation — adding one requires an explicit,
  reviewed allowlist entry, never inferred from a request.

## What this means concretely for the v26.8.19 ticket set

None of the real engineering work named in `01`-`04` (writing AWS SDK client code, registering
an Entra ID app, implementing a Pub/Sub subscriber, parameterizing a Helm chart, provisioning CI
secrets) maps onto `run_inventory_components` or `get_castle_jobs`. Those two capabilities
observe and lightly probe the already-shipped platform; they do not author new source files,
call external cloud SDKs, or provision infrastructure. Claiming gymact "actuates" the
marketplace-listing work would be asserting a capability this session's own code does not have
— a violation of the no-overclaiming discipline this repo's own `CLAUDE.md`-equivalent rules
require.

## What autofde-lab actually is, checked against its own `CLAUDE.md`

autofde-lab's real planning architecture (`src/autofde_lab/fabric/pddl_engine.py`) produces a
real PDDL plan via a real `Astar` solver, and `powl.py` projects that plan into a real POWL2
Turtle document with real blake3 digests. Both steps are real and already verified elsewhere in
this repo's history. But autofde-lab's own `CLAUDE.md` states, unhedged: **"Projection is not
execution... no component in the portfolio executes a POWL plan end to end."** A PDDL domain
for "finish the AWS entitlement adapter" or "draft an EULA" would be a real, well-formed plan —
and then nothing in this codebase would execute a single step of it. Building such a domain for
this ticket set would produce a plan artifact with no actuator behind it, which is a worse
outcome than not building one: it would look like progress while adding zero real capability.

## What is honestly recommended instead

1. **Do not force this ticket set's engineering work through gymact or autofde-lab.** The
   ordinary agentic-coding path (an agent or a human directly authoring the AWS SDK client,
   Helm templates, EULA draft) is the real, working mechanism — the same mechanism that
   produced every one of the 44 revenue capabilities and the chart wrap this session already
   shipped, verified by `tsc --noEmit` and `helm lint`/`helm template`, not by a planner.
2. **If a genuinely new, narrow Castle verb becomes worth adding** — for example, a real
   `castle marketplace-scan-status` subcommand that reports the CI scan-gate's last real run
   result — that would be a legitimate future extension of `ALLOWED_CASTLE_VERBS`, reviewed like
   any other allowlist change, and then a real new gymact capability. This is a possible
   follow-up, not a claim that it exists today.
3. **"Simulating time passing"**, if the goal is genuinely to model the external-clock items
   (KYC review, marketplace certification queues) as first-class objects rather than prose, is
   better served by a real backward-chain document like this one — stating the finished premise,
   then the real current gap, then the real estimated external duration — than by asking a tool
   with no time-simulation capability to pretend to have one. That is what `01`-`04` of this
   ticket set already do.
