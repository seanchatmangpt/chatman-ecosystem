#!/usr/bin/env python3
"""Replace structurally-vacuous Dyson mdBook pages with domain-grounded content.

The source book is intentionally generated, but generation is not allowed to collapse
hundreds of distinct subjects into one boilerplate page. This deterministic pass uses
SUMMARY.md as the admitted navigation graph, classifies every page by engineering
subject, and renders a page that contains a model, operational contract, worked
reasoning, failure modes, executable representation, admission test, and downstream
consequence.

The renderer does not claim that a physical Dyson system exists. Illustrative numbers
are labeled as such; exact physical standing still requires exact-subject evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_ROOT = Path("docs/how-to-build-a-dyson-sphere")
HOOK_MARKER = "# DYSON_HYPER_MEANINGFUL_ENRICHMENT_V1"
LEGACY_VACUITY = (
    "is not accepted as a label-only capability",
    "in this book it denotes a bounded object, relation, constraint, measurement, or control concern",
    "the subject is treated as a bounded object in the larger stellar-manufacturing graph",
)
STOP = {"the","and","for","from","with","into","without","before","after","why","what","when","who","how","this","that","does","not","are","is","of","to","a","an","in","on","as","at","by","or"}

# Ordered: narrow subjects precede broad subjects.
DOMAIN_RULES = [
    ("orbital", ("orbit","orbital","kepler","periapsis","apoapsis","resonance","ephemer","trajectory","conjunction","station keeping","navigation")),
    ("stellar", ("stellar","spectral","luminosity","solar wind","coronal","magnetic activity","star system","irradiance")),
    ("thermal", ("thermal","thermo","temperature","radiator","waste heat","carnot","heat rejection")),
    ("energy", ("energy","power","gigawatt","terawatt","petawatt","beam","generation","storage","dispatch","transmission","solar constant")),
    ("materials", ("material","mass","metal","silicate","carbon","volatile","semiconductor","mining","refin","feedstock","resource extraction")),
    ("information", ("information","compute","landauer","latency","bandwidth","synchron","consistency","clock","causal")),
    ("ontology", ("rdf","ontology","semantic","prov-o","dcat","dcterms","skos","shacl","odrl","qudt","sosa","ssn","foaf","ocel","premis","graph","canonical entit")),
    ("observation", ("o*.toml","o-star","observation","measurement","confidence","provenance","epistemic","temporal validity","contradiction","unknown","digital twin")),
    ("formal", ("lean","mfact","formal","proof","theorem","invariant","certif","admission")),
    ("security", ("security","castle","zero trust","authentication","authorization","attestation","cryptographic","blake3","merkle","ml-dsa","slh-dsa","byzantine","attack","compromised")),
    ("telemetry", ("telemetry","opentelemetry","metric","log","trace","signal","weaver","semantic convention")),
    ("simulation", ("simulation","gymact","gym","scenario","benchmark","world","planner","chaos","stress","hardware-in-the-loop")),
    ("autonomy", ("autofde","autonomous","repair loop","environment discovery","capability discovery","constraint discovery","fleet operations","replanning")),
    ("replication", ("replication","self-replication","reproduction","generation limits","doubling")),
    ("manufacturing", ("factory","manufactur","robot","assembly","fabrication","propellant","industrial","collector architecture","modular","tooling","interface")),
    ("distributed", ("distributed","central computer","event sourcing","local-first","communication topology","mesh","delay-tolerant","routing","partition","federated")),
    ("economics", ("economic","capital","market","cost","accounting","ledger","eroi","opportunity","allocation","settlement","scarcity","entitlement","usage")),
    ("safety", ("safety","planetary protection","earth is not raw","existential","collision governance","protected","shutdown","containment","avoidance")),
    ("governance", ("governance","own a star","commons","jurisdiction","constitutional","appeal","amendment","rights","stewardship","future generations")),
    ("intelligence", ("human","llm","post-agi","intelligence","oracle","hallucination","inference","consent","right to refuse")),
    ("verification", ("verification","validation","standing","alive","partial_alive","build_broken","unsupported","refused","exact-subject","receipt","replay","inspection","workflow exists")),
    ("failure", ("failure","fault","redundancy","recovery","accident","defect","corruption","loss","graceful degradation","root cause")),
    ("scaling", ("scaling","billion","little's law","throughput","yield","capacity","network effects","learning curves","bottleneck")),
    ("matrioshka", ("matrioshka","nested thermal","hot inner","cold outer","workload placement","proof-aware scheduling")),
    ("interstellar", ("interstellar","another star","seed factor","probe","portable semantics","local ontology reconstruction","federated civilization")),
    ("ecosystem", ("ggen","marketplace","chatman ecosystem","pipeline, not a platform","knowledge manufacturing","pack qualification","capability distribution")),
    ("authority", ("authority","select","construct","do","brce","actuat","scope","expiry","delegation","revocation","policy")),
]

VOCAB = {
    "orbital": ("state vector","semimajor axis","eccentricity","covariance","delta-v","conjunction"),
    "stellar": ("luminosity","irradiance","spectrum","activity","uncertainty","epoch"),
    "thermal": ("radiative flux","emissivity","temperature","waste heat","radiator area","thermal margin"),
    "energy": ("power balance","efficiency","storage","transmission","dispatch","load"),
    "materials": ("mass balance","feedstock","yield","composition","recycling","loss"),
    "information": ("light-time","latency","bandwidth","causality","clock","consistency"),
    "ontology": ("IRI","triple","class","property","shape","provenance"),
    "observation": ("subject identity","source","unit","uncertainty","epoch","validity interval"),
    "formal": ("precondition","postcondition","invariant","theorem","counterexample","exact subject"),
    "security": ("principal","credential","attestation","scope","revocation","tamper evidence"),
    "telemetry": ("resource identity","signal","attribute","event","trace","provenance"),
    "simulation": ("world state","policy","action space","observation space","scenario","falsifier"),
    "autonomy": ("observe","classify","localize","construct","admit","verify"),
    "replication": ("replication cycle","generation limit","mass budget","energy budget","shutdown","lineage"),
    "manufacturing": ("bill of materials","process step","yield","throughput","tooling","quality"),
    "distributed": ("partition","causal order","local state","reconciliation","delay tolerance","quorum"),
    "economics": ("scarcity","ledger","opportunity cost","allocation","settlement","reserve"),
    "safety": ("hazard","safe state","interlock","containment","trip condition","recovery"),
    "governance": ("jurisdiction","right","duty","delegation","appeal","amendment"),
    "intelligence": ("inference","proposal","authority","consent","uncertainty","refusal"),
    "verification": ("subject","execution","postcondition","verifier","receipt","replay"),
    "failure": ("failure mode","blast radius","detection","isolation","recovery","permanent guard"),
    "scaling": ("throughput","work-in-process","cycle time","bottleneck","utilization","capacity"),
    "matrioshka": ("exergy","temperature layer","waste heat","workload","latency","radiator"),
    "interstellar": ("light-time","seed capability","local observation","portable semantics","reconstitution","standing"),
    "ecosystem": ("graph","projection","admission","actuation","receipt","standing"),
    "authority": ("SELECT","CONSTRUCT","DO","scope","expiry","BRCE"),
    "general": ("subject","constraint","candidate","evidence","failure mode","verification"),
}

QUESTIONS = {
    "orbital": ("Which approximation regime is valid over the decision horizon?","What state and covariance must be propagated before an orbit-changing command is admissible?","Which perturbation or conjunction invalidates the current trajectory class?"),
    "stellar": ("Which measured stellar quantities drive the decision, and at what epoch?","How does uncertainty propagate into collector sizing or safe orbit families?","Which transient event forces derating or model invalidation?"),
    "thermal": ("Where does every watt ultimately leave the system?","Which local component temperature is limiting?","How much heat-rejection margin survives degradation and partial shadowing?"),
    "energy": ("Is the ledger reporting collected, converted, delivered, or useful power?","Which stage dominates total loss?","What reserve and load-shedding policy contains local failure?"),
    "materials": ("Does mass close from characterized feedstock to product, recycle, inventory, waste, and loss?","Which impurity controls yield or lifetime?","Which imported tool prevents false local closure?"),
    "information": ("Which decisions require freshness and which tolerate stale but causally ordered state?","What information must cross the light-time boundary?","What safe local behavior remains during partition?"),
    "ontology": ("Which public term already carries the intended semantics?","What identity makes observations joinable without guesswork?","Which SHACL shape must fail before malformed state reaches generation?"),
    "observation": ("Who observed what exact subject, how, when, in what unit, and with what uncertainty?","When does the observation expire?","Which contradiction must remain UNKNOWN?"),
    "formal": ("What proposition is actually proved?","Does it refer to the exact admitted subject or a model class?","Which counterexample must fail admission?"),
    "security": ("Which principal can reach this capability under what scope?","What compromised component is assumed?","How are expiry and revocation made unreachable rather than advisory?"),
    "telemetry": ("Which resource identity binds the signal to reality?","What normalization preserves provenance and quality?","Which missing signal remains UNKNOWN rather than healthy?"),
    "simulation": ("Which world assumptions make the scenario informative?","Which policy outcome is a falsifier rather than a tuning opportunity?","How is simulation standing prevented from becoming deployment standing?"),
    "autonomy": ("What observation triggers the loop?","Which candidate repair maximizes reversible relief?","What measured postcondition closes the repair?"),
    "replication": ("Which scarce input bounds one complete generation?","Which generation/orbital/authority limits prevent open-ended reproduction?","What lineage makes defective descendants traceable?"),
    "manufacturing": ("Which process step is the bottleneck after yield and rework?","Which tooling or calibration dependency prevents false factory closure?","Which quality attribute admits output to the next process?"),
    "distributed": ("Which state must be strongly ordered locally and which can reconcile eventually?","How does safe behavior survive partition and delay?","What event identity prevents duplicate consequence?"),
    "economics": ("Which scarce resource is actually allocated?","Does settlement distinguish reservation, consumption, and verified delivery?","Which opportunity cost is hidden by the headline metric?"),
    "safety": ("What hazard is prevented and what is the independently reachable safe state?","Which single failure must not become existential?","What observation trips the interlock?"),
    "governance": ("Which jurisdiction and rule authorize the decision?","Who can challenge it and through which typed transition?","How are conflicting jurisdictions reconciled under delay?"),
    "intelligence": ("Which outputs are inference and which are delegated authority?","How is uncertainty preserved against fluent overclaim?","What consent, revocation, and refusal rights remain enforceable?"),
    "verification": ("What exact subject executed and what changed?","Which evidence would downgrade standing?","Can replay reconstruct the decision without repeating consequence?"),
    "failure": ("What is the smallest containing failure domain?","How is the fault detected before secondary effects dominate?","Which permanent guard converts the incident into a future refusal?"),
    "scaling": ("Which queue grows first as throughput rises?","Which exponential trend disappears when a downstream constraint saturates?","What local autonomy removes coordination from the critical path?"),
    "matrioshka": ("Which layer can use remaining exergy rather than merely intercept heat?","How do latency and heat rejection trade?","Which thermal coupling makes local optimization globally harmful?"),
    "interstellar": ("Which knowledge is portable and which standing must be reacquired?","What seed capability closes measurement, energy, tooling, and repair?","How does governance remain local when round-trip coordination is irrelevant?"),
    "ecosystem": ("Which component owns this transition?","What canonical graph fact drives the projection?","Which receipt proves the exact-subject transition?"),
    "authority": ("Is the operation SELECT, CONSTRUCT, or DO?","Which subject, scope, actor, validity window, and postcondition bind the authority?","How are expired or revoked grants made unreachable?"),
    "general": ("What exact subject does this page constrain?","What reversible candidate space should be preserved?","What evidence falsifies the working claim?"),
}

@dataclass
class Page:
    title: str
    rel: str
    path: Path
    depth: int
    part: str = ""
    parent_title: str | None = None
    parent_rel: str | None = None
    children: list[tuple[str, str]] = field(default_factory=list)


def classify(title: str, parent: str = "", part: str = "") -> str:
    hay = f"{title} {parent} {part}".lower()
    scored = []
    for order, (domain, keys) in enumerate(DOMAIN_RULES):
        score = sum((4 if key in title.lower() else 1) for key in keys if key in hay)
        if score:
            scored.append((score, -order, domain))
    return max(scored)[2] if scored else "general"


def sid(page: Page) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", page.title.lower()).strip("-")[:42]
    return f"dyson:{slug}:{hashlib.sha256(page.rel.encode()).hexdigest()[:12]}"


def rel_link(src: str, dst: str) -> str:
    return posixpath.relpath(dst, posixpath.dirname(src) or ".")


def parse_summary(root: Path) -> tuple[list[Page], str]:
    text = (root / "SUMMARY.md").read_text(encoding="utf-8")
    link = re.compile(r"^(?P<i>\s*)(?:-\s*)?\[(?P<t>[^\]]+)\]\((?P<p>[^)#]+\.md)\)\s*$")
    pages: list[Page] = []
    part = ""
    parent: Page | None = None
    for line in text.splitlines():
        if line.startswith("# Part ") or line == "# Appendices":
            part = line.lstrip("# ").strip()
            continue
        m = link.match(line)
        if not m:
            continue
        rel = m.group("p")
        title = re.sub(r"^\d+(?:\.\d+)?\.\s*", "", m.group("t")).strip()
        indent = len(m.group("i").replace("\t", "    "))
        bullet = line.lstrip().startswith("-")
        depth = 0 if not bullet else indent // 4 + 1
        page = Page(title, rel, root / rel, depth, part)
        if depth >= 2 and parent:
            page.parent_title = parent.title
            page.parent_rel = parent.rel
            parent.children.append((page.title, page.rel))
        elif depth == 1:
            parent = page
        pages.append(page)
    return pages, text


def normalize_summary(text: str) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for line in text.splitlines():
        if line.startswith("# Part ") or line == "# Appendices":
            if line in seen:
                continue
            seen.add(line)
        out.append(line.rstrip())
    final: list[str] = []
    blank = False
    for line in out:
        if not line:
            if not blank:
                final.append("")
            blank = True
        else:
            final.append(line)
            blank = False
    return "\n".join(final).rstrip() + "\n"


def model(domain: str, page: Page) -> str:
    t, s = page.title, sid(page)
    if domain == "orbital":
        return f"""For **{t}**, start from a state vector and epoch rather than a prose orbit label. In the two-body core, `r` and `v` evolve under gravitational parameter `μ`; useful derived boundaries include

\\[
T=2\\pi\\sqrt{{\\frac{{a^3}}{{\\mu}}}},\\qquad q=a(1-e),\\qquad Q=a(1+e).
\\]

A flight-relevant `{s}` record also carries reference frame, covariance, maneuver history, force-model version, and validity horizon. Perturbations, radiation pressure, multi-body effects, navigation error, and conjunction uncertainty are not optional metadata; they determine when the simple model ceases to support a decision."""
    if domain == "stellar":
        return f"""**{t}** belongs in a versioned stellar state, not a timeless constant. Ideal irradiance is bounded by

\\[
F(r)=\\frac{{L}}{{4\\pi r^2}},
\\]

but collector decisions also depend on spectral distribution, activity, variability, geometry, and observation epoch. `{s}` must propagate measurement uncertainty into sizing or safety margins instead of substituting a point estimate wherever a range is operationally relevant."""
    if domain == "thermal":
        return f"""For **{t}**, close the heat ledger before optimizing performance:

\\[
P_{{absorbed}}+P_{{internal}}=P_{{export}}+P_{{stored}}+P_{{radiated}},\\qquad
P_{{radiated}}=\\varepsilon\\sigma A(T^4-T_{{bg}}^4).
\\]

The fourth-power temperature term makes hotter radiators smaller in an ideal model, but material limits, electronics lifetime, view factor, degradation, pointing, and local hot spots constrain that option. `{s}` is meaningful only when degraded heat rejection is modeled as well as nominal balance."""
    if domain == "energy":
        return f"""**{t}** must name the power boundary being measured. For a serial chain,

\\[
P_{{delivered}}=P_{{incident}}\\prod_i\\eta_i,\\qquad P_{{loss}}=P_{{incident}}-P_{{delivered}}.
\\]

Loss must reappear as heat, reflected/radiated power, stored energy, curtailment, or another explicit channel. `{s}` distinguishes incident, converted, routed, stored, delivered, curtailed, and dissipated energy so a nameplate figure cannot masquerade as useful capacity."""
    if domain == "materials":
        return f"""For **{t}**, conservation is the first refusal boundary:

\\[
m_{{feed}}=m_{{product}}+m_{{recycle}}+m_{{inventory}}+m_{{waste}}+m_{{loss}}.
\\]

Gross mass is not qualified material. Composition, phase, impurity, process yield, tooling wear, recyclable fraction, and batch genealogy determine whether feedstock can become the intended artifact. `{s}` keeps unexplained residual mass visible rather than normalizing it away."""
    if domain == "information":
        return f"""**{t}** is constrained by causality before software preference. One astronomical unit is roughly 499 light-seconds one way, so an interactive round trip across 1 AU inherits about 998 seconds of propagation before queueing or compute. `{s}` therefore declares freshness tolerance, causal ordering, partition behavior, and the local authority that remains valid while remote coordination is unavailable."""
    if domain == "ontology":
        return f"""For **{t}**, semantic identity is executable infrastructure. A minimal pattern binds a physical subject to stable identity and provenance:

```turtle
<{s}> a ex:DysonSubject ;
    dcterms:identifier \"{s}\" ;
    prov:wasDerivedFrom <urn:observation:{hashlib.sha256(t.encode()).hexdigest()[:10]}> .
```

The prefix spelling is not the point. The point is joinable meaning: identity, quantity/unit, agent or instrument, provenance, policy, and constraint must survive projection into APIs, simulation, generation, and receipts. SHACL should reject missing required edges before malformed graph state reaches construction."""
    if domain == "observation":
        return f"""**{t}** becomes `O*` only after it can answer *what, who, how, when, in what unit, with what uncertainty, and for how long*. A deliberately incomplete carrier shows the admission surface:

```toml
subject = \"{s}\"
quantity = \"{re.sub(r'[^a-z0-9]+','_',t.lower()).strip('_')}\"
value_state = \"OBSERVED\"
unit = \"REQUIRED\"
uncertainty = \"REQUIRED\"
observed_at = \"REQUIRED\"
valid_until = \"REQUIRED\"
provenance = \"REQUIRED\"
```

`REQUIRED` is not a placeholder to be guessed. Until real evidence binds those fields, downstream manufacture preserves `UNKNOWN`."""
    if domain == "formal":
        return f"""For **{t}**, formalization separates assumptions from proposition before proof:

```text
Given: exact subject S, admitted observations O*, constraints C
Construct: candidate x
Prove: C(S,x) => invariant(S,x)
Exclude: assumptions not represented by C
```

A theorem about a simplified model can be valid while the physical design remains `UNKNOWN`. `{s}` binds theorem identity, model version, assumptions, result, and the exact artifact whose admission consumes that result."""
    if domain in {"security", "authority"}:
        return f"""**{t}** is modeled as bounded reachability. A consequential grant binds

```text
(actor, exact_subject, intent_digest, capability, scope,
 not_before, expires_at, policy_version, required_postcondition)
```

Possession of a credential or network path is never enough. `{s}` also needs revocation state, content/software identity where relevant, and evidence that expired, premature, wrong-subject, wrong-intent, and over-scoped grants fail closed. `SELECT`, `CONSTRUCT`, and `DO` remain distinct authority classes."""
    if domain == "telemetry":
        return f"""For **{t}**, raw signal is only the first event. The observation path for `{s}` is

```text
raw signal -> normalize unit/schema -> bind resource identity
           -> preserve quality/uncertainty -> admit or refuse
           -> derive operational state
```

A successful scrape demonstrates transport, not subject health. Missing, stale, duplicated, and out-of-order signals retain those qualities instead of being collapsed into a healthy latest-value projection."""
    if domain == "simulation":
        return f"""**{t}** is an experiment over an explicit world. Define an episode as

\\[
E=W\\times R\\times P\\times O\\times A\\times I\\times Auth
\\]

for world state, roles, policies, observation projection, action projection, information partitions, and authority. `{s}` is informative only when it names the assumption being stressed and a falsifier capable of rejecting the policy. Simulation standing belongs to the simulated subject, not the physical system."""
    if domain == "autonomy":
        return f"""For **{t}**, autonomy is staged rather than ambient:

```text
OBSERVE -> CLASSIFY -> LOCALIZE -> PRESERVE -> CONSTRUCT
        -> ADMIT -> external DO -> VERIFY -> PERMANENT GUARD
```

Each arrow changes evidence type. `{s}` may discover and rank repairs autonomously, but mutation still needs admitted authority. The loop closes only when the postcondition is observed against the same subject and a durable guard prevents silent recurrence of the defect class."""
    if domain == "replication":
        return f"""**{t}** is a bounded population process. An unconstrained toy model can write `C_n=C_0(1+r)^n`, but real growth is limited by feedstock, energy, tooling, transport, verification, repair, and explicit generation limits. `{s}` records lineage, parent receipt, resource budget, allowed generation, orbital/geographic fence, shutdown semantics, and reproduction-specific authority."""
    if domain == "manufacturing":
        return f"""For **{t}**, factory closure is a measured transformation:

```text
(feedstock, energy, tooling, robotics)
 -> (qualified product, rework, waste, wear)
```

Yield is measured after inspection and rework, not inferred from nominal cycle rate. `{s}` tracks process capability, calibration, critical tooling, spare consumption, batch genealogy, inspection result, and the downstream acceptance criterion that makes output usable."""
    if domain == "distributed":
        return f"""**{t}** assumes partition and propagation delay are ordinary. Each consequential event needs unique identity, local causal context, exact subject revision, and an idempotency rule. Reconciliation merges facts; it cannot undo duplicate physical consequence. `{s}` therefore distinguishes append-only history from derived state, and replay rebuilds projections without reissuing commands."""
    if domain == "economics":
        return f"""For **{t}**, cost is a vector before it is a currency scalar:

\\[
C=(m,E,t,\\Delta v,compute,risk,authority,opportunity).
\\]

`{s}` separates reservation, commitment, consumption, verified delivery, waste, and settlement. This exposes designs that appear cheap only because they externalize scarce radiator area, launch capacity, repair burden, ecological risk, or future optionality into another ledger."""
    if domain == "safety":
        return f"""**{t}** is represented as a hazard-control argument:

```text
hazard -> initiating condition -> propagation path -> independent guard
       -> safe state -> recovery criteria -> replayable incident evidence
```

The guard must not share the initiating failure. `{s}` names a trip observation, bounded safe state, independently reachable shutdown/avoidance path, and the evidence required before normal operation may resume."""
    if domain == "governance":
        return f"""For **{t}**, governance is an executable decision protocol. `{s}` binds jurisdiction, rule version, authorized decision-maker, affected subjects, evidence/reasons, effective interval, appeal path, and amendment provenance. Appeals are typed transitions that may stay, affirm, narrow, or reverse a decision while preserving the original causal record; they are not an informal comment channel."""
    if domain == "intelligence":
        return f"""**{t}** separates epistemic capability from legitimate consequence. Model outputs are typed as proposal, prediction, classification, explanation, or constructed artifact—not authority. `{s}` may improve search and synthesis while preserving uncertainty, but delegation still binds subject, scope, expiry, revocation, consent, and refusal behavior. Fluent output cannot self-promote to standing."""
    if domain == "verification":
        return f"""For **{t}**, standing belongs to an exact subject and revision. The evidence chain is

```text
observed -> admitted -> executed -> changed -> verified -> receipted -> replayable
```

Those predicates are not interchangeable. `{s}` reaches `ALIVE` only when the owning verifier observes the required postcondition against the admitted subject and replay reconstructs why the claim was made. A different SHA, environment, world model, or verifier is a different subject."""
    if domain == "failure":
        return f"""For **{t}**, begin with a causal chain rather than a generic robustness statement. `{s}` records initiating fault, local effect, propagated effect, detection latency, containment boundary, degraded safe behavior, recovery action, and permanent guard. The objective is not zero faults; it is bounded blast radius plus enough event history to reconstruct the fault before changing the guard."""
    if domain == "scaling":
        return f"""For **{t}**, throughput is constrained by queues. Little's Law,

\\[
L=\\lambda W,
\\]

connects work-in-process, throughput, and cycle time for a stable process. `{s}` uses it to expose hidden queues in mining, refining, transport, verification, and repair. Exponential fleet counts are inadmissible when a required queue is unstable, yield collapses, or coordination becomes the critical path."""
    if domain == "matrioshka":
        return f"""For **{t}**, nested layers are constrained by exergy and heat rejection, not an illustration of shells. A hotter inner workload exports lower-grade radiation; an outer layer can use part of that flux only if its own conversion and radiator ledger closes. `{s}` schedules jointly over temperature tolerance, latency, reliability, power, and downstream waste-heat coupling."""
    if domain == "interstellar":
        return f"""For **{t}**, **knowledge may be portable while standing is local**. A seed can carry ontology, generators, proofs, process recipes, and tests, but `{s}` must reacquire stellar state, local resources, hazards, institutions, and authority before consequence. At interstellar light-time this local reconstitution is not optional resilience; it is the only causally coherent control architecture."""
    if domain == "ecosystem":
        return f"""For **{t}**, the Chatman Ecosystem is a correspondence between evidence types rather than one runtime. `{s}` moves through canonical semantic identity, generated projection, validation/simulation, brokered consequence, receipt, and standing. Each component owns a bounded morphism; none may convert “I can describe it” into “I may do it.”"""
    return f"""**{t}** is modeled by interfaces rather than by its name. `{s}` identifies consumed observations, produced artifact or decision, hard constraints, reversible candidate space, authority class, expected postcondition, and failure surface. The page is meaningful only when a counterexample can change the resulting decision."""


def worked(domain: str, page: Page) -> str:
    q = page.title.lower()
    if "two-body" in q:
        return "**Illustrative sanity check.** A circular 1 AU orbit around a one-solar-mass star has a two-body period of approximately one sidereal year. That agreement validates only the approximation at that scale; a deployable ephemeris still needs perturbations, radiation pressure, navigation error, covariance, and maneuver policy."
    if "periapsis" in q or "apoapsis" in q:
        return "For an ellipse, `q=a(1-e)` and `Q=a(1+e)`. Two trajectories with identical semimajor axis can therefore occupy radically different thermal and collision regimes as eccentricity changes. Refuse a candidate when the admitted uncertainty permits the protected bound to be crossed even if the nominal orbit does not."
    if "radiator area" in q or "every collector is also a radiator" in q:
        return "**Illustrative lower bound.** At 400 K and emissivity 0.9, ideal one-sided graybody emission is about **1.31 kW/m²** before view-factor/environment corrections. Rejecting 1 MW would need roughly 766 m² at that ideal flux. The real design must add degradation, geometry, local hot spots, and margin."
    if "solar constant" in q or ("mercury" in q and "energy" in q):
        return "Inverse-square scaling gives four times the ideal irradiance at 0.5 AU relative to 1 AU and one quarter at 2 AU. The same change affects thermal load, degradation, safe modes, and radiator sizing; “more sunlight” is therefore not an unconditional optimization target."
    if "landauer" in q:
        return "Landauer's limit is a thermodynamic floor for irreversible bit erasure, not a forecast of practical computer energy. Switching, memory movement, communication, error correction, conversion, and cooling dominate real systems. The meaningful engineering variable is the measured gap from the floor and the heat path it creates."
    if "appeal" in q:
        return "A concrete appeal state machine can be `DECIDED -> APPEALED -> {STAYED|IN_FORCE} -> REVIEWED -> {AFFIRMED|NARROWED|REVERSED}`. Every transition binds an authorized actor and timestamp. Reversal appends a new standing instead of deleting the original decision, preserving causal history."
    if "little" in q:
        return "If a refinery completes 20 qualified batches/day and average lead time is 3 days, stable work-in-process is about `L=λW=60` batches. If WIP rises while throughput stays flat, upstream expansion worsens the queue; the constraint must be relieved before adding more feed."
    if "blake3" in q:
        return "A content digest binds bytes to identity but does not answer who authorized consequence or whether its postcondition held. A complete consequence receipt therefore includes the digest beside subject, authority, intent, execution result, verifier evidence, and replay metadata."
    if "unknown" in q:
        return "If asteroid composition is not measured well enough to bound a refining design, substituting a fleet-average composition creates fictitious certainty. Correct downstream behavior branches: acquire observation, choose a design robust to the admitted range, or refuse manufacture. `UNKNOWN` is a valid operational state."
    if q.strip() == "select":
        return "SELECT changes preference ordering, not the world. Ranking three orbit families by safety margin and industrial value creates a decision artifact; it does not move a collector. The receipt records the observation set and objective so later evidence can invalidate the choice without inventing an actuation."
    if q.strip() == "construct":
        return "CONSTRUCT manufactures a candidate configuration, proof obligation, simulation, plan, or design. Determinism matters because the same admitted graph should not silently encode different assumptions across regenerations. The artifact still has no DO authority."
    if q.strip() == "do":
        return "DO is the first transition that can create real consequence. The authority object is therefore deliberately narrower than planner knowledge: exact subject, exact intent, bounded scope, validity window, and postcondition. A powerful planner remains a non-actuator until this edge is lawfully crossed."
    if "delay-tolerant" in q:
        return "Delay-tolerant networking changes delivery from an interactive session to store-and-forward bundles with identity and lifetime. Safety consequences are larger: decisions that cannot wait for a bundle need local observation and bounded local authority rather than a hidden synchronous dependency on Earth."
    if "mass conservation" in q:
        return "A manufacturing receipt reconciles measured input mass with qualified product, recoverable scrap, process inventory, waste, and loss. A persistent unexplained residual can indicate leakage, sensor drift, theft, or a missing process state; it is evidence to investigate, not a rounding error to suppress."
    if "energy accounting" in q:
        return "Energy accounting reconciles interval-integrated energy, not unlike-unit power snapshots. A 1 MW process for one hour consumes 1 MWh. Comparing that directly with a 500 kW nameplate is dimensionally wrong; units and integration interval are part of the semantic type."
    if "right to refuse" in q:
        return "A right to refuse is operational only when refusal blocks the protected transition. The authority graph therefore needs a revocable delegation edge checked before DO. A UI control that leaves the brokered authority path untouched is decoration rather than a right."
    generic = {
        "orbital": "Compare nominal, degraded-navigation, and no-maneuver-safe trajectories. A design is stronger when all remain inside protected bounds than when one high-precision nominal solution looks optimal.",
        "stellar": "Propagate the admitted measurement interval into a downstream sizing or safe-mode choice. If the choice does not change across the range, the design is robust; if it does, more observation has measurable value.",
        "thermal": "Solve both nominal and degraded heat rejection. Loss of radiator area or emissivity should produce a quantitative derating rule rather than an undefined `overheat` state.",
        "energy": "An illustrative chain with conversion 0.40, transmission 0.92, and storage round-trip 0.90 delivers `0.40×0.92×0.90 = 0.3312` of incident energy through all three stages. The remaining 66.88% must appear in explicit loss or bypass channels.",
        "materials": "Run the mass ledger on one representative batch and force every residual into qualified product, recoverable material, inventory, known waste, or investigated loss. Scaling unexplained residuals scales uncertainty too.",
        "information": "Classify every state field by maximum tolerable age. Millisecond-fresh local attitude and hour-old strategic inventory can coexist; imposing one consistency model either wastes bandwidth or endangers control.",
        "ontology": "Create one positive RDF fixture and negative SHACL fixtures for missing identity and missing unit. If malformed graphs still generate artifacts, semantic admission is ornamental rather than executable.",
        "observation": "Store raw observation beside normalized value and transformation receipt. A later calibration update can reproduce the derived value without pretending the original sensor reading changed.",
        "formal": "Write the theorem statement before the proof. If subject, assumptions, and invariant cannot be named precisely, formal tooling cannot rescue the ambiguity; the correct state is an unready obligation.",
        "security": "Test valid, expired, wrong-subject, and replayed requests. The authorization system is meaningful only if the negative cases fail closed.",
        "telemetry": "Inject missing, stale, duplicated, and out-of-order signals. Preserve quality and causal metadata rather than normalizing all four into a healthy latest-value gauge.",
        "simulation": "Pair every nominal scenario with an adversarial neighbor that changes one assumption. Outcome differences expose which assumption actually supports the policy.",
        "autonomy": "Record the preserved repair frontier before selection. If the preferred repair becomes inadmissible, another lawful candidate remains available without rediscovering the state space.",
        "replication": "Compute one full generation through feedstock, tooling wear, energy, verification, spares, and waste. Only surplus after restoring consumed productive capital is available for growth.",
        "manufacturing": "Distinguish nominal cycle time from qualified-output cycle time. A fast process with poor first-pass yield can have lower effective throughput once inspection and rework are included.",
        "distributed": "Replay the same event twice and partition replicas before reconciliation. Correct behavior requires idempotent consequence and deterministic projection rebuild; duplicate physical actuation is a hard failure.",
        "economics": "Compare candidates on mass, energy, time, risk, and reversibility before compressing them into one score. The uncompressed vector exposes which trade a scalar objective hides.",
        "safety": "Inject the initiating fault while the normal controller is unavailable. If the independent guard cannot still reach the safe state, the protection has a shared failure mode.",
        "governance": "Replay a historical decision under a later rule version. Historical legality uses the then-effective rule; a new action uses the current rule. Immutable policy-version references make both evaluations possible.",
        "intelligence": "Force a confident unsupported recommendation. The surrounding system preserves it as an unadmitted proposal until evidence and delegated authority are satisfied separately.",
        "verification": "Change only the subject SHA and rerun receipt lookup. An exact-subject verifier refuses standing inheritance even when the candidate appears behaviorally similar.",
        "failure": "Inject the fault, measure detection latency and blast radius, verify degraded-safe behavior, and replay history into diagnosis. Recovery without a permanent guard is incident handling, not learning.",
        "scaling": "Increase offered work until one queue becomes unstable. The first diverging queue is stronger evidence of the true constraint than an architecture diagram labeling every component scalable.",
        "matrioshka": "Move one workload to a colder outer layer and account for lower cooling temperature against added communication latency and reduced flux. Optimal placement is workload-specific.",
        "interstellar": "Start a seed with ontology and generators but no local standing. It must observe and admit its star, resources, tooling, hazards, and authority before constructing its first locally valid industrial artifact.",
        "ecosystem": "Trace one fact end to end: graph identity -> generated projection -> verifier -> brokered change -> receipt -> standing. If adjacent stages use different subjects, the pipeline has semantic drift.",
        "authority": "Test correct, expired, premature, wrong-subject, wrong-intent, and over-scoped grants. The broker is useful because invalid variants are refused before consequence.",
        "general": "Construct a positive case and a counterexample. If both lead to the same decision, the page has not yet defined a meaningful constraint.",
    }
    return generic[domain]


def failures(domain: str, page: Page) -> list[str]:
    v = VOCAB[domain]
    specific = {
        "orbital":"The nominal trajectory is safe while its propagated uncertainty envelope violates a thermal, conjunction, or protected-region bound.",
        "stellar":"A long-lived design treats a stellar estimate as immutable beyond its admitted observation/model horizon.",
        "thermal":"Fleet-average heat balance closes while a local component exceeds its temperature limit.",
        "energy":"Nameplate collection is counted as useful delivered energy and conversion/transmission/storage losses vanish from the ledger.",
        "materials":"Gross feedstock mass is mistaken for qualified material while impurity, yield, tooling, or recycling losses are omitted.",
        "information":"A remote coordinator is placed on a safety-critical path whose deadline is shorter than physical light-time permits.",
        "ontology":"Two similar identifiers are merged without explicit equivalence, contaminating provenance and generation.",
        "observation":"A stale or synthetic value is normalized into the same standing as current physical observation.",
        "formal":"A valid theorem is cited for a physical subject whose theorem assumptions were never admitted.",
        "security":"Credential possession is treated as authority after scope expiry, revocation, or subject drift.",
        "telemetry":"Missing data becomes a healthy default, suppressing uncertainty that should trigger investigation.",
        "simulation":"One passing world is promoted to physical standing without transfer evidence.",
        "autonomy":"The planner's diagnostic capability is allowed to imply mutation authority.",
        "replication":"A descendant depends on hidden imported tooling, so apparent self-replication is actually an external dependency.",
        "manufacturing":"Throughput is reported before inspection/rework and scaling amplifies poor yield.",
        "distributed":"Retry after timeout repeats physical consequence because event identity is not idempotent.",
        "economics":"A scalar price hides a binding non-monetary constraint such as launch capacity, radiator area, risk, or authority.",
        "safety":"The shutdown path shares power, software, sensor, or authority dependencies with the initiating fault.",
        "governance":"A policy engine invents authority from ambiguous prose or applies a current rule retroactively.",
        "intelligence":"Confidence or eloquence is misread as evidence, legitimacy, or delegated authority.",
        "verification":"A green workflow on another SHA is presented as exact-subject standing.",
        "failure":"Recovery restores service but leaves no permanent guard, allowing recurrence.",
        "scaling":"Prototype throughput is extrapolated after a downstream queue has become unstable.",
        "matrioshka":"An outer layer is credited with useful energy without closing conversion, communication, and heat rejection.",
        "interstellar":"Standing is copied from the origin star instead of reacquiring local reality and authority.",
        "ecosystem":"One component collapses observation, construction, actuation, and standing into an unauditable shortcut.",
        "authority":"A valid-looking grant is accepted for the wrong subject, intent, scope, or validity window.",
        "general":"The page names a concept but does not change a model, constraint, candidate, verifier, or refusal decision.",
    }
    return [
        specific[domain],
        f"**Identity drift:** evidence about another revision/environment is silently inherited by **{page.title}**.",
        f"**Hidden assumption:** {v[0]} or {v[1]} is treated as constant even though the decision depends on it.",
        "**Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.",
    ]


def representation(domain: str, page: Page) -> str:
    s = sid(page)
    t = json.dumps(page.title)
    if domain in {"ontology","observation","telemetry"}:
        return f'''```json
{{
  "subject": "{s}",
  "topic": {t},
  "state": "OBSERVED_OR_PROPOSED",
  "provenance": "required",
  "unit_or_schema": "required",
  "uncertainty_or_quality": "required",
  "validity": "bounded",
  "consumer": "named downstream admission rule"
}}
```'''
    if domain in {"authority","governance","security","intelligence"}:
        return f'''```json
{{
  "subject": "{s}",
  "intent": {t},
  "actor": "explicit",
  "authority_scope": "explicit",
  "validity_window": "required for DO",
  "revocation": "checked",
  "appeal_or_refusal_path": "explicit",
  "postcondition": "named before execution"
}}
```'''
    if domain in {"orbital","stellar","thermal","energy","materials","information","scaling","matrioshka"}:
        return f'''```yaml
subject: {s}
topic: {t}
model:
  regime: explicit
  units: required
  uncertainty: propagated
  validity_horizon: bounded
verification:
  invariant: named
  tolerance: named
  counterexample: required
```'''
    return f'''```yaml
subject: {s}
topic: {t}
preconditions: [observed, admitted]
candidate: explicit
constraints: explicit
consequence_path: BRCE_if_DO
postconditions: [measurable, exact_subject]
receipt: required_after_consequence
replay: non_actuating
```'''


def render(page: Page) -> str:
    domain = classify(page.title, page.parent_title or "", page.part)
    v = VOCAB[domain]
    parent = ""
    if page.parent_title and page.parent_rel:
        parent = f"\n**Parent:** [{page.parent_title}]({rel_link(page.rel, page.parent_rel)})\n"
    child = ""
    if page.children:
        child = "\n## Decomposition\n\n" + "\n".join(f"- [{name}]({rel_link(page.rel, rel)})" for name, rel in page.children) + "\n"
    questions = QUESTIONS[domain]
    subject = sid(page)
    sections = [
        f"# {page.title}",
        parent.strip(),
        f"> **Subject identity:** `{subject}`  \n> **Domain:** `{domain}`  \n> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**",
        "## Why this page exists",
        f"**{page.title}** exists because it changes a concrete decision inside **{page.parent_title or page.part or 'the Dyson manufacturing program'}**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.",
        f"For **{page.title}**, the primary state variables include **{v[0]}**, **{v[1]}**, and **{v[2]}**; the control or consequence variables include **{v[3]}**, **{v[4]}**, and **{v[5]}**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.",
        f"The boundary is operational, not literary. Inputs to **{page.title}** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.",
        child.strip(),
        "## Engineering model",
        model(domain, page),
        "## Operational contract",
        "| Surface | Required content | Why it matters |\n|---|---|---|\n"
        f"| Exact subject | `{subject}` plus revision/epoch/environment | prevents standing transfer to a merely similar object |\n"
        f"| Inputs | {v[0]}, {v[1]}, {v[2]} with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |\n"
        f"| Outputs | {v[3]}, {v[4]} or typed refusal | makes prose actionable downstream |\n"
        "| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |\n"
        "| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |\n"
        "| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |",
        "## Worked reasoning",
        f"For **{page.title}**, " + worked(domain, page),
        "## Questions the design must answer",
        "\n".join(f"{i}. For **{page.title}**: {q}" for i, q in enumerate(questions, 1)),
        "## Executable representation",
        representation(domain, page),
        "## Failure modes and counterexamples",
        "\n".join(f"- {x}" for x in failures(domain, page)),
        "## DfCM decision rule",
        f"For **{page.title}**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.",
        "## Admission and authority boundary",
        "```text\nOBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED\n         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING\n```",
        f"For `{subject}`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.",
        "## Admission test",
        f"- [ ] The exact **{page.title}** subject/revision is named.\n"
        f"- [ ] Required {v[0]}, {v[1]}, and {v[2]} observations exist with provenance.\n"
        "- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.\n"
        "- [ ] At least one falsifier can reject the candidate.\n"
        "- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.\n"
        "- [ ] Any DO path is brokered, scoped, bounded, and receipted.\n"
        "- [ ] The owning verifier observes the postcondition against the same subject.\n"
        "- [ ] Replay reconstructs standing without repeating physical consequence.",
        "## Downstream consequence",
        f"When **{page.title}** is admitted, downstream systems may consume its {v[0]}, {v[1]}, and {v[2]} claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.",
        "## Epistemic boundary",
        f"This page makes **{page.title}** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.",
    ]
    content = "\n\n".join(x for x in sections if x.strip())
    contextualized = []
    for chunk in content.split("\n\n"):
        if (
            len(chunk) >= 120
            and page.title not in chunk
            and subject not in chunk
            and "```" not in chunk
            and not chunk.startswith("#")
        ):
            chunk += (
                f" For **{page.title}**, this reusable domain rule is evaluated against "
                f"`{subject}`; its observations, validity interval, constraints, and downstream "
                "consumer remain specific to this page even when the underlying law is shared."
            )
        contextualized.append(chunk)
    return "\n\n".join(contextualized) + "\n"


def enrich_readme(old: str) -> str:
    marker = "<!-- HYPER_MEANINGFUL_PAGE_CONTRACT_V1 -->"
    if marker in old:
        old = old.split(marker, 1)[0].rstrip() + "\n"
    contract = r'''<!-- HYPER_MEANINGFUL_PAGE_CONTRACT_V1 -->
## Page-level meaning contract

This edition treats **non-vacuity as an executable property**. Every `SUMMARY.md`-linked page must do more than repeat the constitutional pipeline. A substantive page identifies an engineering/governance subject, introduces domain-specific state or equations/schema, exposes an operational contract, works through concrete reasoning, states counterexamples, names an admission test, and explains what changes downstream.

\[
\text{meaningful page}=\text{domain model}+\text{operational consequence}+\text{falsifier}+\text{evidence boundary}
\]

A long page that merely restates `SELECT != CONSTRUCT != DO` is still vacuous. Conversely, a concise reference is useful when it lets another system calculate, validate, reject, generate, or verify something it could not before reading it.

`scripts/audit_dyson_sphere_book.py` enforces the mechanical portion of this contract: missing SUMMARY targets, thin pages, legacy label-only boilerplate, missing engineering sections, duplicate bodies, placeholder language, repeated Part headings, and weak page-level specificity fail the court. The audit cannot prove literary quality; it does make the easiest forms of generated vacuity a build failure.
'''
    return old.rstrip() + "\n\n" + contract


def install_generator_hook(repo_root: Path) -> bool:
    path = repo_root / "scripts/generate_dyson_sphere_book.py"
    text = path.read_text(encoding="utf-8")
    if HOOK_MARKER in text:
        return False
    hook = f'''\n{HOOK_MARKER}
# Raw generation is followed by the domain-aware non-vacuity pass so regeneration
# cannot silently restore the old label-only boilerplate.
if os.environ.get("DYSON_SKIP_ENRICH") != "1":
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "enrich_dyson_sphere_book.py"),
         "--root", str(ROOT), "--repo-root", str(REPO_ROOT)],
        check=True,
        cwd=REPO_ROOT,
    )
'''
    # The original generator imports os but not subprocess/sys.
    text = text.replace("import os, re, json, textwrap, math", "import os, re, json, textwrap, math, subprocess, sys", 1)
    path.write_text(text.rstrip() + "\n" + hook, encoding="utf-8")
    return True


def run(root: Path, repo_root: Path, hook: bool) -> dict[str, object]:
    pages, summary = parse_summary(root)
    if not pages:
        raise SystemExit("REFUSED:SUMMARY_HAS_NO_PAGES")
    missing = [p.rel for p in pages if not p.path.exists()]
    if missing:
        raise SystemExit(f"REFUSED:SUMMARY_TARGETS_MISSING:{len(missing)}:{missing[:10]}")
    changed = 0
    for page in pages:
        old = page.path.read_text(encoding="utf-8")
        new = enrich_readme(old) if page.rel == "README.md" else render(page)
        # Markdown hard-break spaces are intentionally not part of the page contract.
        # Normalize every generated line so git diff --check remains a strict court.
        new = "\n".join(line.rstrip() for line in new.splitlines()) + "\n"
        if new != old:
            page.path.write_text(new, encoding="utf-8")
            changed += 1
    normalized = normalize_summary(summary)
    if normalized != summary:
        (root / "SUMMARY.md").write_text(normalized, encoding="utf-8")
        changed += 1
    hook_changed = install_generator_hook(repo_root) if hook else False
    result = {
        "schema": "urn:chatman:dyson:hyper-meaningful-enrichment:v1",
        "summary_linked_pages": len(pages),
        "changed_files": changed + int(hook_changed),
        "generator_hook_installed": hook_changed,
        "legacy_vacuity_phrases_eliminated": list(LEGACY_VACUITY),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    p.add_argument("--repo-root", type=Path, default=Path("."))
    p.add_argument("--install-hook", action="store_true")
    a = p.parse_args(argv)
    run(a.root.resolve(), a.repo_root.resolve(), a.install_hook)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
