#!/usr/bin/env python3
"""Manufacture substantive content for published pages identified as vacuous.

This is a deterministic semantic-enrichment stage, not a word-count padder.
It is intentionally constrained to pages surfaced by audit_doc_vacuity.py.
For each weak page it appends or, for known duplicated Chateco appendices,
replaces content with a subject-specific operational contract containing:

* why the concept exists in the system;
* the invariant or semantic contract it carries;
* how it composes with observation/admission/construction/actuation;
* concrete failure modes and falsifiers;
* the evidence required before standing can be promoted.

The Dyson corpus is generator-owned. This script is designed to be invoked by
scripts/generate_dyson_sphere_book.py after its primary projection so enriched
appendices remain reproducible projections rather than hand-edited output.

Usage:
    python3 scripts/enrich_published_pages.py --write
    python3 scripts/enrich_published_pages.py --write --scope docs/how-to-build-a-dyson-sphere
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import audit_doc_vacuity

ROOT = Path(__file__).resolve().parents[1]
MARKER = "<!-- semantic-enrichment:v1 -->"


def title_for(path: Path, text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    stem = path.stem.replace("-", " ").replace("_", " ")
    return re.sub(r"\s+", " ", stem).strip().title()


def slug_words(path: Path, title: str) -> set[str]:
    raw = f"{path.as_posix()} {title}".lower().replace("_", "-")
    return set(re.findall(r"[a-z0-9]+", raw))


def domain(path: Path, title: str) -> str:
    words = slug_words(path, title)
    p = path.as_posix()
    if p.startswith("books/hditc/"):
        return "hditc"
    if p.startswith("docs/chateco-phd/"):
        return "chateco"
    if "404" in words:
        return "navigation"
    if words & {"orbit", "orbital", "radiative", "energy", "mass", "reliability", "replication", "equations", "mathematical"}:
        return "physics"
    if words & {"ontology", "classes", "properties", "shapes", "mappings", "units", "shacl"}:
        return "ontology"
    if words & {"o", "star", "toml", "observation", "world", "solar", "collector"} and "receipt" not in words:
        return "observation"
    if "receipt" in words or "receipts" in words:
        return "receipt"
    if words & {"ggen", "pack", "manifest", "templates", "validators", "queries", "tests"}:
        return "manufacture"
    if words & {"gymact", "agent", "policy", "episode", "reward", "objective"}:
        return "simulation"
    if words & {"brce", "admission", "authority", "actuation", "replay", "refusal"}:
        return "authority"
    if words & {"unknown", "alive", "blocked", "broken", "unsupported", "status", "taxonomy"}:
        return "standing"
    if "failures" in words or "failure" in words or "catalogue" in words:
        return "failure"
    if words & {"availability", "safety", "slos", "manufacturing", "repair"}:
        return "slo"
    if words & {"sparql", "query", "queries"}:
        return "query"
    if words & {"lean", "mfact", "certification"}:
        return "formal"
    if words & {"deployment", "earth", "lunar", "asteroid", "mercury", "swarm", "testbed"}:
        return "deployment"
    if words & {"glossary", "symbols", "notation"}:
        return "reference"
    if words & {"research"}:
        return "research"
    if words & {"contributors", "license", "readme", "read"}:
        return "meta"
    if "ocel" in words:
        return "process"
    if words & {"interface", "projection", "matrix"}:
        return "interface"
    if words & {"memory", "civilization", "algebra"}:
        return "memory"
    return "general"


DOMAIN_TEXT = {
    "physics": (
        "This page is a physical admission boundary, not a decorative formula sheet. "
        "A civilization-scale design is lawful only when every generated configuration can be traced back to measurable quantities, units, uncertainty, and a model whose domain of validity is stated. The governing rule is that physics constrains manufacture before optimization: no planner score, simulation success, or economic preference may override conservation laws, orbital stability, thermal balance, or reliability bounds.",
        "Treat each equation or scaling relation as a typed contract. Inputs need units and provenance; outputs need uncertainty and a validity interval; approximations need an explicit regime. A useful computation therefore has the form `observation -> normalized quantity -> model -> bounded prediction -> admission decision`. Where the model is only approximate, the result stays bounded rather than being promoted to exact truth. At stellar scale this distinction prevents small modeling assumptions from silently becoming fleet-wide authority.",
        "The strongest falsifier is an independently observed state outside the admitted envelope: an orbit that violates separation bounds, an energy ledger that does not close, a mass balance with unexplained loss, a thermal state beyond material limits, or a replication curve that assumes unavailable feedstock. Such a result revokes the design's standing and forces re-observation or a narrower model; it is not an invitation to tune the verifier until the design passes."
    ),
    "ontology": (
        "This page defines semantic interoperability, not vocabulary for its own sake. The ontology layer gives independently implemented systems a common meaning for objects, relations, quantities, constraints, authority, and evidence. That meaning must survive transport across RDF stores, generators, simulators, formal checkers, telemetry pipelines, and runtime adapters without a repository-specific interpretation becoming the hidden source of truth.",
        "The operational contract is `public meaning -> local extension -> SHACL/admission -> generated projection`. Classes identify what a thing is; properties state relations or measurements; QUDT-style units prevent dimension confusion; SHACL shapes turn semantic assumptions into executable constraints; mappings preserve correspondence to external standards. An extension is lawful only when it narrows or composes public semantics rather than redefining them incompatibly.",
        "A useful ontology page names its failure modes. Two systems using the same label with different units, a class whose identity cannot be reconciled, a property whose domain/range is ambiguous, or a shape that accepts an invalid state are semantic defects. The falsifier is a concrete graph that should be rejected but passes, or a valid graph that cannot round-trip through the declared mapping. Those examples belong in tests because semantic drift is otherwise invisible until actuation."
    ),
    "observation": (
        "This page belongs to the observation boundary: it explains how a real subject becomes an admitted, replayable description rather than an unqualified bag of facts. Observation is always partial. The carrier must bind exact subject identity, measurement time, source provenance, units, uncertainty, contradiction state, and the dimensions that remain UNKNOWN. A digest identifies the carrier; it does not make the carrier true.",
        "The operational sequence is `raw signal -> normalization -> provenance -> contradiction handling -> O* admission`. A value can be syntactically present yet inadmissible because its source is stale, its units are unresolved, or another source contradicts it. The critical rule is that UNKNOWN is preserved as topology. Missing knowledge may remove candidate actions from the lawful frontier, but it cannot be converted into permission merely because a planner prefers progress.",
        "Falsifiers are identity drift, stale observations reused against a changed subject, loss of provenance, contradictory measurements collapsed without a rule, and a regenerated observation whose digest cannot be reproduced from the same admitted inputs. Any of these lowers standing. The recovery path is re-observation and re-admission, not manual assertion that the old world model is still close enough."
    ),
    "receipt": (
        "A receipt is the boundary between an assertion that work happened and evidence that a particular consequential transition has standing. It must bind the exact subject, admitted intent, authority, pre-state, attempted mutation, post-state observation, verifier, outcome, and replay identity. Merely naming a JSON object `receipt` is insufficient; the object has to make substitution and ambiguity mechanically detectable.",
        "For consequential DO, reservation precedes actuation. The reservation binds the candidate, subject, authority grant, expected postconditions, and idempotency identity before the external effect is reachable. After actuation, an acknowledgement is only transport evidence. DONE requires an observation of the admitted consequence, closure of the authority bound, final receipt persistence, and enough provenance to replay verification without reacquiring actuation capability.",
        "The key falsifiers are receipt-after-effect ordering, missing exact subject identity, a changed post-state inheriting an old receipt, an ambiguous actuator response being blindly retried, or a receipt that verifies after any bound field is altered. A robust schema makes those failures typed. If final persistence fails after an attempt, standing is BLOCKED/AMBIGUOUS with the durable reservation as reconciliation handle—not falsely ALIVE and not automatically retried."
    ),
    "manufacture": (
        "This page is part of the semantic manufacturing pipeline. The durable asset is the knowledge needed to regenerate an artifact: ontology, query, constraints, template, dependency identity, admission rules, and verification procedure. Generated files are projections. Treating a projection as the canonical editing surface creates drift because the next generation pass can erase an apparently valid manual repair.",
        "A lawful manufacturing path is `graph -> query -> deterministic transform -> candidate artifact -> structural admission -> runtime verification -> receipt`. Every stage should have an explicit input identity and a falsifier. Manifests bind dependency closure; templates make construction repeatable; validators reject malformed candidates; tests challenge behavior; receipts bind what actually executed. None of these alone is proof of production behavior, but together they prevent the generator from self-attesting.",
        "The strongest maintenance test is regeneration from a clean checkout. If the same admitted inputs do not reproduce the same semantic artifact, if a required dependency is ambient rather than declared, or if a generated file must be manually patched to pass, the manufacturing system is not closed. The repair belongs upstream in the graph/query/template/validator, followed by regeneration and exact-head verification."
    ),
    "simulation": (
        "This page defines a simulation contract rather than a claim that simulated success equals reality. A gym world must state its entities, state variables, actions, observation projections, information partitions, roles, policies, objective functions, authority boundaries, stochastic processes, and termination conditions. Without those dimensions a score is uninterpretable because the benchmark does not say what information or power the policy had.",
        "The useful algebra is `Episode = World × Roles × Policies × InformationPartitions × Authority`. Planner, policy, role, and agent remain distinct: a planner proposes; a policy maps admitted observations to candidate actions; a role describes responsibilities; an agent is an actor with bounded capabilities. Reward is evidence about the objective encoded by the environment, not permission to actuate outside it.",
        "Simulation is falsified by reality-model mismatch, leakage of privileged observations, an action projection that grants authority the real system does not have, reward hacking, nondeterministic fixtures without recorded seeds, or a scenario suite that excludes the failure class being claimed. The output should therefore include world identity, seed, policy identity, observation/action projections, result metrics, and a receipt that lets another runner reproduce the episode."
    ),
    "authority": (
        "This page sits on the irreversible boundary between choosing a possibility and changing the world. SELECT, CONSTRUCT, and DO are separate authorities. Search may explore many reversible candidates; construction may manufacture an artifact or counterfactual; only an explicitly admitted grant for the exact subject and consequence class can authorize DO. Access to a connector, credential, model, or command runner is capability—not authority.",
        "The brokered sequence is `intent -> exact-subject admission -> authority check -> consequence bound -> receipt reservation -> actuator -> observation -> reconciliation -> final receipt`. Relevant UNKNOWN refuses before DO. Ambiguous actuation does not turn into a retry loop. Replay verifies prior evidence and intentionally lacks an actuator edge. These separations keep autonomous operation from becoming ambient permission.",
        "Permanent falsifiers include accepting a nearby authority class, allowing a grant for one subject to mutate another, invoking an actuator before reservation is durable, promoting transport ACK to DONE, or letting a planner/model/hook manufacture its own authority. Any such edge is a constitutional defect even if the resulting state happens to be desirable."
    ),
    "standing": (
        "Standing is a type over evidence, not a progress adjective. UNKNOWN means the required observation has not closed. PARTIAL_ALIVE means some bounded behavior has executed but the requested crown has not. ALIVE is reserved for the exact admitted subject executing successfully against the required verifier. BLOCKED identifies a known external or authority obstruction; BUILD_BROKEN names a concrete build failure; UNSUPPORTED says the requested capability is outside the implementation; typed REFUSED records a lawful denial.",
        "Statuses do not automatically promote. Source inspection cannot produce ALIVE; the existence of a workflow cannot produce ALIVE; a unit test cannot crown a real integration; a simulation cannot crown deployment. Promotion requires evidence whose subject, environment, command, verifier, and result intersect the claim. Demotion is equally important: changed identity, stale evidence, failed replay, or a newly observed contradiction lowers standing rather than being hidden by a previous green run.",
        "A status page is useful when it tells the reader exactly what evidence would change the type. For each state, name the missing edge, the next lawful observation or execution, and the falsifier. This makes status operational: another system can decide whether to observe, repair, refuse, or re-run without interpreting a vague confidence score."
    ),
    "failure": (
        "Failure is part of the modeled state space, not an exception that disappears from the architecture diagram. This page classifies a particular failure surface so the system can distinguish observation failure, admission refusal, construction defects, actuation ambiguity, verification failure, and authority failure. Those classes demand different recovery behavior and must never be collapsed into a generic retry.",
        "The recovery pattern is `detect -> bind exact subject -> classify -> localize -> construct reversible repair -> admit -> actuate if authorized -> observe -> encode permanent guard`. Detection evidence should survive the repair. If the failure involved an ambiguous external effect, reconciliation precedes any new attempt. If it involved invalid authority, no technical workaround is a lawful substitute for obtaining a valid grant.",
        "A failure catalogue earns its place when every entry has a discriminating signal and a permanent falsifier. Examples include stale pre-state, violated constraint, missing idempotency key, transport timeout after possible actuation, mismatched postcondition, or receipt-integrity failure. The permanent guard should reproduce the original defect and fail before the fix, then pass after it, so the lesson becomes executable knowledge rather than incident folklore."
    ),
    "slo": (
        "This page turns a desirable property into an operational service objective. A useful SLO names the measured subject, numerator, denominator, observation window, sampling method, allowed exclusions, error budget, and consequence of breach. Without those fields a target such as 'safe', 'available', or 'reliable' cannot be falsified and therefore cannot govern an autonomous fleet.",
        "Civilization-scale objectives must also define locality. A global average can hide catastrophic regional failure, so availability, safety, energy delivery, manufacturing yield, repair latency, observation freshness, and receipt completeness should be measurable per cell/fleet/authority domain and aggregatable upward. Measurement itself is an admitted process with provenance; telemetry loss is not equivalent to perfect performance.",
        "A breach should drive a bounded control response rather than an unbounded optimizer. Exhausted error budget can halt expansion, reduce actuation authority, shift capacity to repair, or force a narrower operating envelope. The falsifier is straightforward: construct a trace that violates the stated objective and verify that the control plane detects the breach and takes the declared response."
    ),
    "query": (
        "A query in this architecture is an executable question against a canonical graph. It should expose a decision-relevant slice of reality without smuggling authority into retrieval. SPARQL can find available material, unsafe orbital regions, missing receipts, unresolved constraints, or bottlenecks; the query result is an observation candidate that still requires provenance and admission before it influences consequential DO.",
        "Useful examples state the assumed vocabulary, input graph shape, returned variables, and why each result matters. Queries should be deterministic over the same graph snapshot and should fail visibly when required predicates or units are absent. Negative queries are especially valuable: asking for violations, missing evidence, or contradictions turns governance doctrine into a continuously executable diagnostic surface.",
        "The query layer is falsified by a known counterexample the query misses, by duplicate/ambiguous identities that change the result without detection, or by unit/temporal mismatches that are silently joined. A regression fixture should contain both matching and non-matching graph fragments so a query change cannot broaden or narrow its semantics accidentally."
    ),
    "formal": (
        "Formal admission separates a generated claim from a mechanically checked invariant. The useful pattern is `ggen renders; Lean admits; mfact certifies`: generation constructs a candidate, a proof system checks a precisely stated property, and certification binds the checked claim to the exact artifact identity. A theorem about an abstract model is not automatically a theorem about the deployed artifact; the correspondence edge must be explicit.",
        "Formal properties should focus on consequences that are expensive to discover at runtime: conservation, authority non-escalation, state-machine reachability, receipt completeness, bounded resource use, and impossibility of forbidden transitions. Assumptions belong in the theorem interface rather than prose footnotes. If the proof relies on an admitted constant or model approximation, that dependency becomes part of the receipt.",
        "The critical falsifier is correspondence failure: the proved object differs from the generated or executed subject. Other failures include `sorry`/axiom escape hatches, unbound external assumptions, or a certificate that can be replayed against a changed artifact. Certification therefore binds theorem identity, checker/toolchain identity, artifact digest, assumptions, and verification result."
    ),
    "deployment": (
        "This page describes a deployment stage as a change in the evidence available to the program, not merely a geographic destination. Earth development, orbital testbeds, lunar industry, asteroid factories, Mercury-scale networks, and an inner-system swarm each expose different latency, energy, material, thermal, communication, and recovery constraints. A design that is ALIVE in one environment does not inherit that standing in the next.",
        "Every stage needs entry criteria, bounded authority, reversible experiments, exit evidence, and an abort path. Early deployment should maximize information gain per irreversible consequence: instrument first, validate local models, prove repairability, then expand capacity. Replication authority is explicitly bounded by resource budgets, geofenced/orbit-fenced scope, generation limits, and shutdown semantics so successful manufacturing does not imply permission for unbounded reproduction.",
        "Stage promotion is falsified by evidence that the next environment violates an assumption the previous stage depended on—radiation, thermal load, communications delay, material composition, navigation accuracy, or repair latency. Such evidence narrows the operating envelope and may return the program to simulation or construction; it is not a reason to relabel the new environment as equivalent to the old one."
    ),
    "reference": (
        "A reference page is valuable when it removes semantic ambiguity. Terms and symbols here are not alternate prose names; they are stable handles that let equations, ontologies, generators, receipts, telemetry, and formal claims refer to the same concept. Definitions should state scope and, where relevant, units, identity rules, or the distinction from nearby terms that are easy to conflate.",
        "The reference surface should preserve important separations: observation versus admission, capability versus authority, construction versus actuation, acknowledgement versus DONE, receipt versus log entry, replay versus retry, and subject identity versus display name. Symbols should have one meaning within a stated scope, and unit-bearing quantities should use canonical dimensions rather than relying on reader inference.",
        "A useful falsifier is ambiguity under substitution. If two readers can replace a term with different operational meanings and both appear consistent with the reference, the definition is insufficient. Likewise, if a symbol changes dimension across chapters or a status name lacks evidence criteria, the reference has failed its interoperability role and should be tightened."
    ),
    "research": (
        "Further research is not a parking lot for unspecified future work. Each question should identify an unresolved claim, why current evidence is insufficient, the smallest discriminating experiment or formal result, and what observation would falsify the preferred hypothesis. This converts open work into an executable research backlog rather than an aspirational list.",
        "The strongest questions target boundaries where current models may fail: long-horizon orbital interaction, autonomous repair economics, authority under partition, semantic drift across independently evolved implementations, thermal/material aging, fleet-level error budgets, and correspondence between simulation/formal models and physical systems. Each question should preserve multiple candidate explanations until evidence justifies collapse.",
        "Research standing stays UNKNOWN or PARTIAL_ALIVE until the named experiment executes against its admitted subject. A paper, model, or simulation may improve the prior but cannot silently crown a physical claim. Results should be recorded with data/provenance, method identity, assumptions, negative results, and a replay path so future work can build on evidence rather than a remembered conclusion."
    ),
    "meta": (
        "This page is part of the book's trust surface. Meta-documentation should tell a reader what this corpus is, how it is manufactured, where authority lives, how contributions preserve semantic integrity, and which file is legally or operationally canonical. A short administrative page that cannot answer those questions forces readers to infer policy from repository layout, which is exactly the ambiguity this ecosystem tries to eliminate.",
        "Contributions should modify canonical knowledge rather than generated projections, preserve exact-subject evidence, add falsifiers with new claims, and avoid broadening standing beyond executed proof. Attribution records authorship and material intellectual contribution without implying that contributors personally verified every runtime claim. Licensing text in documentation is explanatory only; the repository's authoritative license artifact controls legal terms and must be referenced rather than paraphrased into a competing license.",
        "The maintenance falsifier is reproducibility: a clean checkout should identify the same canonical source, regenerate the same projections, resolve every SUMMARY edge, and pass the documented verification commands. If a reader must know an undocumented convention to build or interpret the book, this page has missed a material part of its purpose."
    ),
    "navigation": (
        "A missing page should be a recovery surface, not a dead end. The 404 page exists inside a documentation system whose pages carry different kinds of standing: constitutional doctrine, current operational snapshots, historical evidence, generated books, and nested handbooks. Recovery therefore means helping the reader re-establish context, not merely returning to a home page.",
        "When a link fails, first return to the Reading Map or SUMMARY-derived navigation, then check the Documentation Inventory for the canonical location and Current Standing for time-sensitive claims. Historical URLs may have moved because generated projections were replaced by canonical sources; that movement does not authorize rewriting old evidence. Search should prefer concepts and exact identifiers over guessed filenames.",
        "A useful 404 also names what it cannot prove. A broken documentation URL says nothing about whether the underlying capability is ALIVE, BLOCKED, or UNSUPPORTED. Documentation navigation and runtime evidence are separate surfaces. If a missing page appears in SUMMARY.md or the canonical build, that is a publication-graph defect and the docs verifier should fail until the edge is repaired."
    ),
    "process": (
        "OCEL-style process evidence models events around multiple participating objects instead of forcing reality into one case identifier. That matters for fleets where one actuation can touch a subject, authority grant, artifact, organization, receipt, and external resource simultaneously. Event identity, object identity, timestamps, activity type, and object relationships must therefore remain first-class and replayable.",
        "The event log is observation, not authority. It can reconstruct causality, measure throughput and waiting, detect conformance violations, and feed process mining, but it cannot retroactively authorize an action. Derived process models must preserve provenance back to events and state which projection or aggregation produced the view. Otherwise a convenient dashboard can silently become a second source of truth.",
        "Falsifiers include orphan events, reused object identities, impossible temporal ordering, missing authority/receipt objects for consequential events, or a replay whose derived process state differs from the original under the same event set. These should be executable integrity checks on the OCEL export/import boundary."
    ),
    "interface": (
        "An interface projection is one view of a capability algebra, not a new owner of the underlying semantics. CLI, HTTP, MCP, A2A, UI, workflow, and library surfaces should project the same capability identity, parameters, authority requirements, refusal modes, evidence, and standing. A surface-specific convenience must not create a privileged path that bypasses admission or receipts.",
        "The projection matrix should therefore answer more than 'is there an endpoint?'. For each capability it should identify transport, input schema, authentication, exact authority class, idempotency semantics, timeout/ambiguity behavior, postcondition verifier, receipt identity, and replay route. Missing cells are explicit UNSUPPORTED/PARTIAL_ALIVE states rather than assumed parity.",
        "The strongest falsifier is semantic non-equivalence: two interfaces invoke what is nominally the same capability but differ in authorization, defaults, validation, or outcome interpretation. Contract tests should run equivalent requests through each available projection and compare normalized intents and receipts, while still preserving transport-specific evidence."
    ),
    "memory": (
        "Civilization memory is the durable accumulation of executable knowledge: admitted observations, public semantics, generators, proofs, policies, receipts, event histories, failure lessons, and replay procedures. It differs from a document archive because the stored knowledge must be able to reconstruct why a claim had standing and what would revoke it.",
        "The memory algebra is append-oriented around evidence and regeneration. New observations may supersede old standing without deleting the old receipt; new generators may replace projections without rewriting historical subjects; derived knowledge records provenance to the facts and transformations that produced it. This lets independent implementations share semantics while retaining local execution histories.",
        "Memory is falsified when a claimed artifact or decision cannot be reconstructed from retained inputs, when provenance breaks across a migration, when an old receipt is applied to a changed subject, or when deletion of a convenience cache destroys the only copy of manufacturing knowledge. The durable layer should make regeneration cheaper than archaeology."
    ),
    "chateco": (
        "This page belongs to the Chateco research program, whose central claim is that high-rate knowledge work can be industrialized only when observation, semantics, manufacture, authority, execution, and evidence are kept distinct. Its content should therefore contribute a discriminating definition, formal claim, empirical question, or registry—not merely restate the thesis vocabulary.",
        "The research correspondence is `claim -> operationalization -> subject -> method -> evidence -> falsifier`. Definitions need boundaries that prevent synonym drift; axioms need explicit assumptions and consequences; registries need identity and qualification fields; research questions need experiments that could prove the preferred explanation wrong. A thesis page that cannot be connected to this chain is structurally present but scientifically weak.",
        "Standing remains bounded by method. A mathematical result establishes only what follows from its assumptions; a repository observation establishes only the inspected subject/ref; a benchmark establishes only the measured environment; and an executed production receipt establishes only its exact consequential subject. The program is strongest when those evidence classes compose without being substituted for one another."
    ),
    "hditc": (
        "HDITC treats intelligence as a system for preserving and transforming high-dimensional possibility without granting the reasoning substrate ambient authority over the world. The book's durable subject is the separation of observation, reversible candidate construction, admission, bounded DO, receipt, and replay. Introductory and administrative pages should make that contract explicit so readers do not mistake 'post-AGI' for unconstrained autonomy.",
        "DfCM provides the search discipline: retain every lawful reversible edge, rank alternatives without manufacturing permission, and delay irreversible collapse until authority and consequence bounds close. The resulting architecture can exploit abundant machine reasoning while keeping exact subject identity, evidence, and physical/institutional constraints authoritative. The model may be cognitively opaque; opacity is never treated as a cryptographic or safety guarantee.",
        "A reader should be able to falsify the book's implementation claims. Relevant UNKNOWN must refuse before DO; nearby authority must not substitute; receipt reservation must precede actuation; acknowledgement must not equal DONE; ambiguity must not cause blind retry; replay must not possess an actuator. These are the executable boundaries that distinguish governed autonomous manufacture from prompt-driven trust."
    ),
    "general": (
        "This page carries a specific node in the ecosystem's knowledge graph. Its job is to make the concept operational: identify the exact subject, state the invariant that constrains lawful behavior, show how the concept composes with adjacent stages, and name evidence that would falsify the claim. A page that merely repeats terminology without those edges is documentation-shaped WIP.",
        "The default correspondence is `observe -> admit -> construct -> verify -> actuate when authorized -> receipt -> replay`. Not every concept participates in every stage, but the page should say where its authority begins and ends. In particular, descriptive knowledge must not acquire actuation power merely because it is machine-readable or generated by a capable model.",
        "Meaning is tested by discrimination. A reader or machine should be able to use this page to decide between at least two nearby states—valid versus invalid, supported versus unsupported, authorized versus unauthorized, observed versus inferred, or completed versus merely acknowledged. The named falsifier and evidence requirement make that distinction executable."
    ),
}


def enrichment_block(path: Path, title: str) -> str:
    kind = domain(path, title)
    p1, p2, p3 = DOMAIN_TEXT[kind]
    return f"""

{MARKER}

## Operational significance

**{title}** is not retained as a label-only reference. {p1}

## System contract

{p2}

## Failure modes and falsifiers

{p3}

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
"""


SPECIAL_REPLACEMENTS: dict[str, str] = {
    "docs/chateco-phd/src/appendices/c-axioms.md": """# Appendix C — Axioms

The Chateco research program uses axioms as explicit assumptions from which later claims may be derived. They are intentionally not definitions: a definition fixes the meaning of a term, while an axiom states a proposition the formal system admits as a starting condition. Conflating those categories makes proofs circular because a desired conclusion can be hidden inside vocabulary.

## Axiom A1 — observation is partial

For any non-trivial operational subject, an observation carrier is a projection of reality rather than reality itself. Therefore absence of a dimension is not evidence of its negation, and a critical UNKNOWN cannot be promoted to permission.

## Axiom A2 — identity precedes standing

Evidence has standing only for the exact subject it binds. Similar repository names, nearby commits, equivalent-looking cloud resources, or regenerated artifacts do not inherit another subject's receipt without an explicit correspondence proof.

## Axiom A3 — capability is not authority

The existence of a transport, credential, tool, model, or actuator establishes capability. Consequential DO additionally requires an admitted grant whose subject and consequence class intersect the attempted transition. Neither planning nor successful construction manufactures that grant.

## Axiom A4 — construction is cheaper than consequence

The factory should preserve reversible candidate variety before irreversible selection. This motivates DfCM: explore and manufacture many lawful alternatives, but collapse to consequential DO only after constraints, authority, cost, and evidence close.

## Axiom A5 — acknowledgement is not completion

An actuator response proves only what the transport contract establishes. DONE requires observation of the expected postcondition on the exact subject, closure of admitted consequence bounds, and a final receipt. Ambiguity remains bounded and cannot justify blind retry.

## Axiom A6 — replay does not reacquire authority

Replay is a verification operation over retained evidence. It may recompute standing for the same admitted subject and state, but it does not possess an actuator edge and cannot use a historical receipt as permission for a new consequential transition.

## Consequences

Together these axioms induce the program's separation of `OBSERVE`, `ADMIT`, `SELECT`, `CONSTRUCT`, `DO`, `RECEIPT`, and `REPLAY`. Any implementation that collapses those stages may still be useful software, but it is not an implementation of the constitutional calculus claimed by this thesis.

## Falsification boundary

These are modeling axioms, not empirical discoveries. Their value is judged by whether systems built under them make stronger, more reproducible distinctions than systems that do not. An empirical program should therefore compare failure rates, ambiguity recovery, evidence completeness, reversibility, and unauthorized consequence across implementations, rather than treating the axioms as self-validating truths.
""",
    "docs/chateco-phd/src/appendices/u-cloud-simulation-protocol.md": """# Appendix U — Cloud Simulation Protocol

Cloud simulation in Chateco is a controlled experiment over an admitted model of a provider surface. It is not a claim that a mock HTTP server, Terraform plan, or API schema is equivalent to AWS, Azure, GCP, Oracle Cloud, or any other live control plane. The protocol exists to make that distinction executable while still extracting high-value evidence before expensive or consequential live tests.

## Subject identity

Every episode binds a provider, service/API version, region or location model, identity/permission model, resource graph, fixture or recorded corpus version, planner/policy identity, and deterministic seed where stochastic behavior exists. A result without those coordinates is not replayable and cannot be compared across runs.

## World construction

The simulated world is assembled from documented request/response schemas, lifecycle state machines, quotas, error classes, dependency relationships, eventual-consistency behavior where modeled, and explicit UNKNOWN dimensions where fidelity is absent. Unsupported behavior must remain `UNSUPPORTED` rather than being filled with a convenient success response.

## Action boundary

Actions are modeled as typed intents such as create, read, update, delete, attach, detach, deploy, or reconcile. The simulation may project their consequences into its world state, but it carries no production credential and does not manufacture real cloud authority. A policy that succeeds only because the simulator grants impossible permissions is a benchmark defect.

## Observation and reward

The observation projection determines what the policy is allowed to know. Reward should measure objective closure—correct resource state, bounded cost, safety, reversibility, or recovery—not merely API call count or absence of exceptions. Hidden provider state may be used by the verifier but must not leak into the policy unless the real interface exposes it.

## Fidelity ladder

1. **Schema fidelity** — request/response and validation behavior.
2. **Lifecycle fidelity** — legal state transitions and dependency ordering.
3. **Failure fidelity** — authorization, quota, conflict, timeout, and partial-failure classes.
4. **Temporal fidelity** — delays, retries, eventual consistency, and long-running operations.
5. **Cross-resource fidelity** — side effects across dependent resources.
6. **Live differential fidelity** — bounded comparison against authorized real API executions.

A simulator may be ALIVE at one rung while remaining PARTIAL_ALIVE for the next. Fidelity is never implied by the word “exact.”

## Differential verification

For operations authorized for live testing, the same normalized intent is executed in simulation and against an isolated live subject. Observations are reduced to a declared comparison projection so volatile provider metadata does not create false mismatches. Every unexplained difference becomes a model defect or an explicit fidelity exclusion.

## Failure and replay

Timeout after possible actuation, asynchronous operation completion, quota exhaustion, credential expiry, provider-side conflict, and stale read-after-write are first-class scenarios. Replay uses the recorded world, seed, intent sequence, and verifier; it does not replay real cloud mutations. Live retries require a fresh authority/idempotency decision at the real boundary.

## Standing

Simulation evidence can crown the simulator and the policy behavior inside its admitted model. It cannot crown a production deployment, billing path, marketplace entitlement, or destructive cloud operation. Those claims require exact-subject live evidence and their own receipts.
""",
}


def repair(path: Path) -> bool:
    full = ROOT / path
    text = full.read_text(encoding="utf-8")
    key = path.as_posix()
    if key in SPECIAL_REPLACEMENTS:
        replacement = SPECIAL_REPLACEMENTS[key].rstrip() + "\n"
        if text == replacement:
            return False
        full.write_text(replacement, encoding="utf-8")
        return True
    if MARKER in text:
        return False
    title = title_for(path, text)
    full.write_text(text.rstrip() + enrichment_block(path, title).rstrip() + "\n", encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", required=True)
    parser.add_argument("--scope", default="", help="optional repository-relative path prefix")
    args = parser.parse_args()

    _metrics, findings, _stats = audit_doc_vacuity.audit()
    paths = sorted({Path(f.path) for f in findings if f.code != "BROKEN_SUMMARY_LINK"})
    if args.scope:
        prefix = args.scope.rstrip("/") + "/"
        paths = [p for p in paths if p.as_posix().startswith(prefix)]

    changed: list[str] = []
    for path in paths:
        if repair(path):
            changed.append(path.as_posix())

    print(f"semantic_enrichment_candidates={len(paths)}")
    print(f"semantic_enrichment_changed={len(changed)}")
    for path in changed:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
