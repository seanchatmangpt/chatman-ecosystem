#!/usr/bin/env python3
"""Native (imperative) evaluator of the nonllm-class-qualification-pack laws.

An independent implementation of the laws that the pack's SPARQL gates (gates/*.rq), the design's
ASK acceptance predicates and the SHACL shapes (shacl/nlb-shapes.ttl) express declaratively. It walks
rdflib triples directly (no SPARQL engine, no SHACL engine), so agreement between this evaluator and
the declarative instruments is the MSA classification-agreement measurement of the benchmark design.

evaluate(graph) -> {law: [violation, ...]} over the laws
  CLASS BOUNDARY CTQ MEASURE MSA SPLIT STANDING FACTOR TRACE PLAN
An empty list for every law means the graph is admitted.
"""
from __future__ import annotations

import re
from decimal import Decimal

import rdflib
from rdflib.namespace import RDF, RDFS

NLB = rdflib.Namespace("https://ggen.dev/nonllm-bench#")
ES = rdflib.Namespace("https://ggen.dev/ontology/evidence-standing#")
SJ = rdflib.Namespace("https://ggen-igniter.dev/ontology/semantic-jira#")
DFLSS = rdflib.Namespace("https://ggen.dev/dflss#")
PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")

LAWS = ("CLASS", "BOUNDARY", "CTQ", "MEASURE", "MSA", "SPLIT", "STANDING", "FACTOR", "TRACE", "PLAN")
CLAIM_STATUSES = {"KNOWN_CANDIDATE", "PRESERVED", "BLOCKED", "NOT_KNOWN", "OUTSIDE_BOUNDARY"}
CHARTS = {"p", "np", "c", "u", "g", "I-MR"}
MSA_STATUSES = {"HOLDS_OBSERVED_DOMAIN", "FAILS", "FAILS_CLOSED", "UNMEASURED"}
SUPPORTS = {"VARIED", "FIXED", "PARTIAL", "UNSUPPORTED"}
TRACE_TYPES = (
    NLB.AcceptancePredicate, NLB.BenchmarkClass, DFLSS.CTQ, NLB.Factor, NLB.MSACourt, NLB.MSAProperty,
    NLB.NearMissCase, NLB.NegativeControlCase, NLB.Stage, NLB.FaultInjectionPoint, NLB.ClassStanding,
    NLB.EvidenceTier, NLB.FractionalFactorialDesign, NLB.BenchmarkFamily, NLB.CapabilityGap,
    NLB.QualificationPlan, NLB.CrownThreshold, NLB.StatisticDefinition, NLB.BoundRequest, NLB.StandingKind,
    NLB.ReceiptFieldSet, NLB.BenchmarkSuite, NLB.PlanEntry, NLB.ReferenceOrder,
)


def _strs(g: rdflib.Graph, s, p) -> list[str]:
    return [str(o) for o in g.objects(s, p)]


def _has(g: rdflib.Graph, s, *preds) -> bool:
    return all(g.value(s, p) is not None for p in preds)


def _dec(term) -> Decimal | None:
    if term is None:
        return None
    try:
        return Decimal(str(term))
    except Exception:
        return None


def _typed(g: rdflib.Graph, node, cls) -> bool:
    return (node, RDF.type, cls) in g


def known_candidates(g: rdflib.Graph) -> list:
    return sorted(c for c in g.subjects(NLB.claimStatus, rdflib.Literal("KNOWN_CANDIDATE")))


def law_class(g: rdflib.Graph) -> list[str]:
    out = []
    kcs = known_candidates(g)
    counted = [c for c in kcs if _typed(g, c, NLB.BenchmarkClass) and g.value(c, NLB.classToolchain) is not None]
    if len(counted) < 5:
        out.append(f"fewer than five KNOWN_CANDIDATE classes ({len(counted)})")
    for c in sorted(g.subjects(RDF.type, NLB.BenchmarkClass)):
        statuses = _strs(g, c, NLB.claimStatus)
        if len(statuses) != 1 or statuses[0] not in CLAIM_STATUSES:
            out.append(f"{c}: claimStatus {statuses} outside the closed set")
    for c in kcs:
        if not _has(g, c, NLB.repairTool, NLB.verifierArgv, NLB.classToolchain, NLB.membershipPredicate):
            out.append(f"{c}: incomplete class identity")
        bases = {str(b) for m in g.objects(c, NLB.membershipClause) for b in g.objects(m, NLB.clauseBasis)}
        if "TYPED_OUTPUT" not in bases:
            out.append(f"{c}: membership without a TYPED_OUTPUT clause")
        if not bases & {"TRIAL_REPAIR", "INDEPENDENT_SEMANTIC"}:
            out.append(f"{c}: membership without a TRIAL_REPAIR or INDEPENDENT_SEMANTIC clause")
        repair_families = {str(f) for t in g.objects(c, NLB.repairTool) for f in g.objects(t, NLB.implementationFamily)}
        iv_families = {str(f) for v in g.objects(c, NLB.independentVerifier) for f in g.objects(v, NLB.implementationFamily)}
        if not any(fv != ft for fv in iv_families for ft in repair_families):
            out.append(f"{c}: no independent verifier of another implementation family")
        near = {
            m for m in g.subjects(NLB.nearClass, c)
            if _typed(g, m, NLB.NearMissCase) and (m, NLB.expectedStanding, ES.UNKNOWN) in g
            and g.value(m, NLB.expectedReason) is not None
        }
        if len(near) < 3:
            out.append(f"{c}: {len(near)} near-misses expecting UNKNOWN (< 3)")
    return out


def law_boundary(g: rdflib.Graph) -> list[str]:
    out = []
    for m in sorted(g.subjects(RDF.type, NLB.NearMissCase)):
        expected = list(g.objects(m, NLB.expectedStanding))
        if expected != [ES.UNKNOWN]:
            out.append(f"{m}: near-miss expects {[str(e) for e in expected]}, not exactly UNKNOWN")
        if g.value(m, NLB.expectedReason) is None:
            out.append(f"{m}: near-miss without a typed reason")
        if g.value(m, NLB.inClass) is not None:
            out.append(f"{m}: near-miss counted as a class member")
    for m in sorted(g.subjects(RDF.type, NLB.NegativeControlCase)):
        expected = list(g.objects(m, NLB.expectedStanding))
        if expected != [ES.REFUSED]:
            out.append(f"{m}: negative control expects {[str(e) for e in expected]}, not exactly REFUSED")
        if g.value(m, NLB.expectedReason) is None:
            out.append(f"{m}: negative control without a typed reason")
        if g.value(m, NLB.inClass) is not None:
            out.append(f"{m}: negative control counted as a class member")
    return out


def law_ctq(g: rdflib.Graph) -> list[str]:
    out = []
    ctqs = sorted(g.subjects(RDF.type, DFLSS.CTQ))
    if len(set(ctqs)) != 15:
        out.append(f"CTQ tree has {len(set(ctqs))} CTQs, not fifteen")
    for q in ctqs:
        if not _has(g, q, PROV.wasDerivedFrom, NLB.operationalMeasure, NLB.verificationMethod, NLB.negativeCase,
                    NLB.controlChart, NLB.requiredResult):
            out.append(f"{q}: CTQ missing an admitted field")
        charts = _strs(g, q, NLB.controlChart)
        if len(charts) > 1 or any(c not in CHARTS for c in charts):
            out.append(f"{q}: control chart {charts} outside the closed set")
    return out


def law_measure(g: rdflib.Graph) -> list[str]:
    out = []
    measured = 0
    for s in sorted(g.subjects(RDF.type, NLB.Stage)):
        if _has(g, s, NLB.ocelEventType, NLB.coversMorphism, NLB.instrumentedToday, NLB.stageOrder):
            measured += 1
        else:
            out.append(f"{s}: RTY stage without its measurement fields")
    if measured != 7:
        out.append(f"{measured} measured RTY stages, not seven")
    required = {"uname_sm", "actuator_toolchain", "factor_levels"}
    if not any(required <= set(_strs(g, r, NLB.requiredField)) for r in g.subjects(RDF.type, NLB.ReceiptFieldSet)):
        out.append("no receipt field set names uname_sm, actuator_toolchain and factor_levels")
    return out


def law_msa(g: rdflib.Graph) -> list[str]:
    out = []
    courts = sorted(g.subjects(RDF.type, NLB.MSACourt))
    for p in sorted(g.subjects(RDF.type, NLB.MSAProperty)):
        covered = [m for m in courts if (m, NLB.msaProperty, p) in g
                   and _has(g, m, NLB.statusToday, NLB.verifierCommand)]
        if not covered:
            out.append(f"{p}: MSA property without a court")
    for m in courts:
        statuses = _strs(g, m, NLB.statusToday)
        if len(statuses) != 1 or statuses[0] not in MSA_STATUSES:
            out.append(f"{m}: MSA status {statuses} outside the closed set")
    return out


def law_split(g: rdflib.Graph) -> list[str]:
    out = []
    for c in known_candidates(g):
        if not _has(g, c, NLB.devRepo, NLB.reachableTier, NLB.reachableTierWithSynthetic, NLB.clusterCount):
            out.append(f"{c}: corpus plan incomplete (Dev(C), reachable tiers, clusters)")
    train = [a for a in g.subjects(NLB["split"], NLB.Train)]
    for b in sorted(g.subjects(NLB["split"], NLB.Test)):
        for a in train:
            if not set(g.objects(a, NLB.inClass)) & set(g.objects(b, NLB.inClass)):
                continue
            if (set(g.objects(a, NLB.subjectDigest)) & set(g.objects(b, NLB.subjectDigest))
                    or set(g.objects(a, NLB.patchId)) & set(g.objects(b, NLB.patchId))):
                out.append(f"{b}: Test member leaks the identity of Train member {a}")
    return out


def law_standing(g: rdflib.Graph) -> list[str]:
    out = []
    rows: dict[tuple[int, int], list[Decimal]] = {}
    for r in g.subjects(RDF.type, NLB.BoundRow):
        n, x, b = g.value(r, NLB.boundN), g.value(r, NLB.boundDefects), _dec(g.value(r, NLB.exactUpperBound))
        if n is not None and x is not None and b is not None:
            rows.setdefault((int(n), int(x)), []).append(b)
    for s in sorted(set(g.subjects(NLB.standingKind, None))):
        kinds = list(g.objects(s, NLB.standingKind))
        state = g.value(s, ES.standingState)
        if any(k != NLB.BENCHMARK_DESIGN_ALIVE for k in kinds):
            if not _has(g, s, NLB.forClass, NLB.tier, NLB.n, NLB.defects, NLB.confidence, NLB.upperFailureBound,
                        NLB.boundMethod, NLB.environmentScope):
                out.append(f"{s}: incomplete evidence tuple")
        if state == ES.ALIVE and any(k in (NLB.NON_LLM_OPERATIONAL_ALIVE, NLB.BENCHMARK_QUALIFIED) for k in kinds):
            if g.value(s, NLB.unseenExecutionReceipt) is None:
                out.append(f"{s}: operational or qualified standing ALIVE without unseen-execution receipts")
        if state == ES.ALIVE and NLB.NON_LLM_OPERATIONAL_ALIVE in kinds:
            ranks = [int(r) for t in g.objects(s, NLB.tier) for r in g.objects(t, NLB.tierRank)]
            if (not any(r >= 1 for r in ranks) or (s, NLB.msaStanding, ES.ALIVE) not in g
                    or rdflib.Literal(0) not in set(g.objects(s, NLB.llmInvocations))
                    or rdflib.Literal(0) not in set(g.objects(s, NLB.replayDivergence))
                    or any(str(g.value(f, NLB.support)) == "UNSUPPORTED" for f in g.objects(s, NLB.variedFactor))):
                out.append(f"{s}: NON_LLM_OPERATIONAL_ALIVE without DISCOVERY-tier evidence, MSA ALIVE, zero LLM, zero replay divergence")
    for s in sorted(set(g.subjects(NLB.n, None))):
        n, d = g.value(s, NLB.n), g.value(s, NLB.defects)
        if n is None:
            continue
        n = int(n)
        if n > 0:
            digests = {str(dg) for r in g.objects(s, NLB.unseenExecutionReceipt) for dg in g.objects(r, NLB.subjectDigest)}
            if len(digests) < n:
                out.append(f"{s}: pseudo-replication (n={n}, {len(digests)} distinct subject digests)")
        if d is None:
            continue
        d = int(d)
        u = _dec(g.value(s, NLB.upperFailureBound))
        exact = rows.get((n, d))
        if u is not None:
            if not exact:
                out.append(f"{s}: no generated BoundRow for (n={n}, x={d})")
            elif any(u < b for b in exact):
                out.append(f"{s}: claimed bound {u} below the exact bound {max(exact)} for (n={n}, x={d})")
        for t in g.objects(s, NLB.tier):
            tn = g.value(t, NLB.tierN)
            tb = _dec(g.value(t, NLB.zeroDefectUpperBound))
            if tn is not None and n < int(tn):
                out.append(f"{s}: n={n} below its tier's N={int(tn)}")
            if tb is not None and exact and any(b > tb for b in exact):
                out.append(f"{s}: exact bound for (n={n}, x={d}) above its tier's zero-defect bound {tb}")
    return out


def law_factor(g: rdflib.Graph) -> list[str]:
    out = []
    listed = {f for f in g.objects(None, NLB.hasFactor)}
    for f in sorted(g.subjects(RDF.type, NLB.Factor)):
        supports = _strs(g, f, NLB.support)
        if len(supports) != 1 or supports[0] not in SUPPORTS:
            out.append(f"{f}: support {supports} outside the closed set")
            continue
        support = supports[0]
        placed = (g.value(f, NLB.column) is not None or g.value(f, NLB.bitWeight) is not None
                  or g.value(f, NLB.generatedBy) is not None or f in listed)
        if support != "VARIED" and placed:
            out.append(f"{f}: {support} factor placed in the design")
        if support == "VARIED" and g.value(f, NLB.bitWeight) is None and g.value(f, NLB.generatedBy) is None:
            out.append(f"{f}: VARIED factor neither base nor generated")
    for f in sorted(listed):
        if str(g.value(f, NLB.support)) != "VARIED" or g.value(f, NLB.column) is None:
            out.append(f"{f}: design factor without a VARIED column")
    return out


def law_trace(g: rdflib.Graph) -> list[str]:
    out = []
    nodes = set()
    for t in TRACE_TYPES:
        nodes |= set(g.subjects(RDF.type, t))
    for node in sorted(nodes):
        targets = list(g.objects(node, PROV.wasDerivedFrom))
        if not any(_typed(g, p, SJ.Proposition) for p in targets):
            out.append(f"{node}: untraced design node")
        for p in targets:
            if not _typed(g, p, SJ.Proposition):
                out.append(f"{node}: trace target {p} is not an operator-prose proposition")
    return out


def law_plan(g: rdflib.Graph) -> list[str]:
    out = []
    for fam in sorted(g.subjects(RDF.type, NLB.BenchmarkFamily)):
        codes = _strs(g, fam, NLB.familyCode)
        if len(codes) != 1 or not re.fullmatch(r"B[1-6]", codes[0]):
            out.append(f"{fam}: family code {codes}")
        if not _has(g, fam, NLB.familyAcceptance, NLB.familyFalsifier):
            out.append(f"{fam}: family without acceptance or falsifier")
        caps = list(g.objects(fam, NLB.familyCapability))
        if len(caps) != 1 or not _typed(g, caps[0], SJ.Capability):
            out.append(f"{fam}: family capability {caps}")
        refs = list(g.objects(fam, NLB.referenceOrder))
        if not refs or not all(_typed(g, r, NLB.ReferenceOrder) for r in refs):
            out.append(f"{fam}: reference orders missing or untyped")
    for gap in sorted(g.subjects(RDF.type, NLB.CapabilityGap)):
        codes = _strs(g, gap, NLB.gapCode)
        if len(codes) != 1 or not re.fullmatch(r"[A-Z][A-Z0-9-]{1,40}", codes[0]):
            out.append(f"{gap}: gap code {codes}")
        if not re.match(r"(UNSUPPORTED|BLOCKED|PARTIAL)", str(g.value(gap, NLB.gapStatus) or "")):
            out.append(f"{gap}: gap status {g.value(gap, NLB.gapStatus)}")
        if not _has(g, gap, NLB.targetRepository, RDFS.label):
            out.append(f"{gap}: gap without target repository or label")
        refs = list(g.objects(gap, NLB.referenceOrder))
        if not refs or not all(_typed(g, r, NLB.ReferenceOrder) for r in refs):
            out.append(f"{gap}: reference orders missing or untyped")
    for m in sorted(g.subjects(RDF.type, NLB.MSACourt)):
        codes = _strs(g, m, NLB.courtCode)
        if len(codes) != 1 or not re.fullmatch(r"M[0-9]{1,2}", codes[0]):
            out.append(f"{m}: court code {codes}")
        refs = list(g.objects(m, NLB.referenceOrder))
        if not refs or not all(_typed(g, r, NLB.ReferenceOrder) for r in refs):
            out.append(f"{m}: reference orders missing or untyped")
    for c in known_candidates(g):
        codes = [x for x in _strs(g, c, NLB.classCode) if re.fullmatch(r"[A-Z][A-Z0-9-]{1,30}", x)]
        if not codes or g.value(c, NLB.targetRepository) is None:
            out.append(f"{c}: class without an upper-case class code or target repository")
    for p in sorted(g.subjects(RDF.type, NLB.QualificationPlan)):
        for prop, cls in ((NLB.planRoot, SJ.GoalCheckpoint), (NLB.planCheckpoint, SJ.GoalCheckpoint),
                          (NLB.msaCapability, SJ.Capability), (NLB.gapCapability, SJ.Capability)):
            vals = list(g.objects(p, prop))
            if len(vals) != 1 or not _typed(g, vals[0], cls):
                out.append(f"{p}: {prop} {vals}")
        prefix = _strs(g, p, NLB.planIdPrefix)
        if len(prefix) != 1 or not re.fullmatch(r"[A-Z][A-Z0-9-]*-", prefix[0]):
            out.append(f"{p}: plan id prefix {prefix}")
        if not _has(g, p, NLB.planNamespace, NLB.planReplayPrefix):
            out.append(f"{p}: plan namespace or replay prefix missing")
    return out


def evaluate(g: rdflib.Graph) -> dict[str, list[str]]:
    return {
        "CLASS": law_class(g),
        "BOUNDARY": law_boundary(g),
        "CTQ": law_ctq(g),
        "MEASURE": law_measure(g),
        "MSA": law_msa(g),
        "SPLIT": law_split(g),
        "STANDING": law_standing(g),
        "FACTOR": law_factor(g),
        "TRACE": law_trace(g),
        "PLAN": law_plan(g),
    }
