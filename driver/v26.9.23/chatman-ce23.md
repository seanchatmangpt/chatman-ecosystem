<!-- Provenance: operator-authored prose pasted into Claude Code session 1fecd79a on 2026-09-23 ~10:50 PT with the directive
     "ultracode — scan the projects to see what else should be added to the loop, remember the goal is not to have you hand
     code wherever possible". Status: operator testimony (O* by fiat). Source text for the CE23 (Chatman Ecosystem v26.9.23)
     requirements; compiled into work orders through the v26.9.23 first-mile pipeline, not hand-authored into a backlog. -->

# Chatman Ecosystem v26.9.23 — release requirements

## Determination

**`Chatman Ecosystem v26.9.23` should be a dependency-closed composition release around the Semantic Manufacturing checkpoint, not an “all repositories green” release.**

The accepted v26.9.23 contract already defines completion as:

$$
STOP_{23}
=
\bigwedge_{i=0}^{12}GC23_i
\land RequiredUnknown=\varnothing
\land RequiredLLM_{KNOWN}=\varnothing
\land RemainingFrontier\subseteq
\{Successor,Blocked,Unsupported,Refused\}
$$

The latest executed local court reached **11/13 ALIVE**: `GC23-0 … GC23-10`. `GC23-11` fleet/release standing and `GC23-12` semantic self-hosting remain open. 

The two critical implementation subjects are now remotely materialized:

* `xaas/friday/gc-fri-0800` → `b4ef5d664cb5afa2ab5456ac20d28500f5b00144`
* `ggen_igniter/friday/gc-fri-0800` → `3937a4f89ecf2b7fa12068406377c05ec1a1b8fc`

The push was verified against the remote and **no PRs were open** at the end of the supplied run.  GitHub currently shows those branches **96 commits** and **193 commits** ahead of their respective `main` branches, with neither behind.

So:

$$
\boxed{
Standing(ChatmanEcosystem@26.9.23)=UNKNOWN
}
$$

There is not yet an admitted `chatman-ecosystem v26.9.23` subject, and the upstream Semantic Manufacturing crown is not yet complete.

## Current evidence state

| Subject             | Current evidence                                                                                                | Standing for v26.9.23                     |
| ------------------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| GC23-0…3            | Prose admission, cold bootstrap, deterministic compiler, complete tuple executed                                | **ALIVE locally**                         |
| GC23-4…10           | SA2A conservation → no-LLM execution → verification → receipt/OCEL → frontier → MachineExperience → cold replay | **ALIVE locally**                         |
| GC23-11             | Requires exact final `xaas` + `ggen_igniter` heads after release PR/merge/requalification                       | **UNKNOWN**                               |
| GC23-12             | V23-H unfinished in supplied run; successor acceptance required                                                 | **UNKNOWN**                               |
| `xaas`              | Release branch pushed at exact SHA; still off `main`; no PR                                                     | **PARTIAL_ALIVE for release**             |
| `ggen_igniter`      | Release branch pushed at exact SHA; still off `main`; no PR                                                     | **PARTIAL_ALIVE for release**             |
| pushed STOP receipt | GitHub branch still contains an older `STOP=false`, `0/13` receipt                                              | **stale / not admissible as final crown** |
| `chatman-ecosystem` | GitHub repo exists at `main`; no v26.9.23 release subject/manifest                                              | **UNKNOWN**                               |
| `ggen-ecosystem`    | Fleet classified its own crown as blocked on Git-LFS AGROVOC smudge                                             | **BLOCKED, noncritical**                  |
| remaining fleet     | 14 Successor, 3 Refused in the v26.9.23 fleet classification                                                    | **lawfully outside critical path**        |

That distinction between local execution and durable remote evidence matters. The local transcript establishes the 11/13 observation; the currently pushed `xaas` branch still has `docs/sjira/v26.9.23/receipts/STOP-GC-26.9.23.json` from the earlier **0/13** run, and `GC23-12.json` still records `UNKNOWN: machinery_absent`. `docs/sjira/v26.9.23/successor/ACCEPTED` is absent. Therefore the local 11/13 result must be re-sealed rather than treated as already published standing.

The release lane itself specifies the correct order: qualify exact integration heads → stop court → PRs → exact-head CI/fix-forward → merge → independently verify → requalify main → release receipt → tag only after reproducible `STOP=true`. 

## Required `chatman-ecosystem v26.9.23` contract

| ID          | Requirement                                        | Admission condition                                                                                                                                                           | Current gap                                                                                                            |
| ----------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **CE23-0**  | **Re-establish root identity**                     | `chatman-ecosystem` working subject is bound to a GitHub remote + exact SHA; lineage is proven rather than inferred                                                           | Overnight fleet classified the local checkout `UNSUPPORTED` because it could not relate it to published GitHub lineage |
| **CE23-1**  | **Create an independent v26.9.23 release subject** | Add `release/v26.9.23/…`; preserve `release/v26.9.1` untouched                                                                                                                | No v26.9.23 release subject exists today                                                                               |
| **CE23-2**  | **Crosswalk the old constitutional graph**         | Every one of the 16 roles required by `release/v26.9.1/manifest.toml` maps explicitly to `REQUIRED`, `SUCCESSOR`, `BLOCKED`, `UNSUPPORTED`, or `REFUSED` for the new boundary | Must not silently erase the old release topology                                                                       |
| **CE23-3**  | **Import the Semantic Manufacturing crown**        | Exact digest of a fresh `STOP-GC-26.9.23` receipt says `STOP=true`, all 13 gate receipts admitted, replay succeeds                                                            | 11/13 observed; pushed STOP receipt stale                                                                              |
| **CE23-4**  | **Close GC23-12**                                  | V23-H manufactures successor prose; its digest is explicitly accepted; self-hosting court passes                                                                              | V23-H unfinished; `successor/ACCEPTED` absent                                                                          |
| **CE23-5**  | **Close GC23-11**                                  | `xaas` and `ggen_igniter` release changes reach exact post-merge `main` SHAs; fleet receipts are regenerated against those identities                                         | Both branches remain off main; no PRs                                                                                  |
| **CE23-6**  | **Preserve fleet typing**                          | Every observed repo is classified; `RequiredUnknown=0`; `UnclassifiedRequiredWork=0`; noncritical failures cannot reopen the release without falsifying a GC23 proposition    | Existing 21-repo matrix supplies the starting projection                                                               |
| **CE23-7**  | **Version-fence Chatman tooling**                  | `verify_release`, portfolio survey/planner, standing verifier, West projection, etc. can explicitly target `release/v26.9.23` rather than silently defaulting to `v26.9.1`    | Multiple current scripts/catalog surfaces default to `release/v26.9.1/...`                                             |
| **CE23-8**  | **Preserve zero-intelligence KNOWN path**          | Imported crown proves `LLM_INVOCATIONS_ON_KNOWN_REFERENCE_PATH=0` and `UNRECEIPTED_ACTUATION=0`                                                                               | Must be carried into root release receipt, not merely documented                                                       |
| **CE23-9**  | **Exact-head root court**                          | Candidate Chatman SHA passes generated-projection drift, manifest/ref validation, unit/integration, imported receipt validation, replay, and strict release crown             | Not manufactured yet                                                                                                   |
| **CE23-10** | **Produce root release receipt**                   | Receipt binds Chatman SHA, xaas SHA, ggen_igniter SHA, graph/ontology/schema/toolchain/provider digests, fleet digest, all gate receipts, replay and exclusions               | Not present                                                                                                            |
| **CE23-11** | **Tag only the crowned subject**                   | `v26.9.23` identifies the exact Chatman release whose imported Semantic Manufacturing STOP replays true                                                                       | Impossible until CE23-3…10 close                                                                                       |

### The important Chesterton fence

The existing `chatman-ecosystem` manifest for `v26.9.1` has **16 required roles**: public ontology, research, process-type law, config admission, manufacture, marketplace, formal proof, CMCA kernel, orchestration, actuation, exploration, process execution, provenance, fleet conformance, product and capstone.

The new Semantic Manufacturing fleet instead says only **`xaas` and `ggen_igniter` are runtime critical for GC-26.9.23**; 14 other observed projects are successors and the remainder are typed outside the boundary. The overnight run explicitly says “making every repository ALIVE” is not a release requirement. 

Those are not contradictory if Chatman v26.9.23 contains an explicit **boundary migration/crosswalk**. They *are* contradictory if we simply replace the old 16-role manifest with a two-repo manifest and pretend the old obligations disappeared.

Therefore I would manufacture:

$$
ReleaseGraph_{23}
=
\{
ChatmanRoot,\;
SemanticManufacturingCrown,\;
FleetClassification,\;
LegacyRoleCrosswalk
\}
$$

with only the subjects actually required by the v26.9.23 checkpoint participating in its conjunctive runtime crown.

## Project disposition for this release

The supplied generated fleet matrix gives the correct initial partition:

**Critical path:** `xaas`, `ggen_igniter`.

**Successor:** `ash_a2a`, `ash_atlassian`, `ash_surface`, `autofde-lab`, `beam4pm`, `engineering-standards`, `ferroplan`, `frozen-duckdb`, `ggen`, `ggen-marketplace`, `gitvan`, `gymact`, `open-ontologies`, `zcode-cli`.

**Blocked but noncritical:** `ggen-ecosystem`.

**Refused from this release boundary:** `remo`, `turbo-fieldfare`, `unjucks`.

**Special case:** `chatman-ecosystem` was marked `UNSUPPORTED` only because the overnight local checkout lacked a usable remote identity relationship. The authenticated GitHub source proves the repository exists and is accessible; v26.9.23 therefore needs to repair **transport/identity**, not “fix” Chatman implementation code merely because of that classification.

WD FA/V23-W should also **not** become a new v26.9.23 blocker. The governing graph places the WD FA first-mile work in the `GC-26.9.24` successor bucket, and live WD integration is explicitly excluded from this release.

## Crown equation

I would make the root court compute exactly this:

$$
\boxed{
CHATMAN\_STOP_{26.9.23}
=
Identity
\land BoundaryCrosswalk
\land SM\_STOP
\land ExactMainHeads
\land FleetClosed
\land KnownPath_{LLM=0}
\land UnreceiptedActuation_{=0}
\land Replay
\land RootReceipt
}
$$

where:

$$
SM\_STOP=\bigwedge_{i=0}^{12}GC23_i
$$

and:

$$
FleetClosed \iff
RequiredUnknown=0
\land UnclassifiedRequiredWork=0.
$$

### Immediate critical path

The shortest lawful path is now:

**V23-H → operator successor-digest acceptance → fresh 12/13 court → V23-Q release lane → PR both critical repos → exact-head CI/fix-forward → merge → requalify → GC23-11 → fresh 13/13 `STOP=true` receipt → manufacture `chatman-ecosystem/release/v26.9.23` → crosswalk old roles → root crown/replay → tag.**

Do **not** spend v26.9.23 closing `ggen-ecosystem`, `autofde-lab`, `ash_surface`, `zcode-cli`, or other successor work unless an observation proves one of those repos is actually traversed by a GC23 court. That would change the topology; until then, it is successor work by construction.
