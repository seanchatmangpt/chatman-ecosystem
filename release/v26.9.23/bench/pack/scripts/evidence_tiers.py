#!/usr/bin/env python3
"""Single-mu statistics kernel of the nonllm-class-qualification-pack: exact evidence-tier bounds.

Reads (bench.toml [kernel].inputs) the pack's tier specifications (nlb:EvidenceTier: tierN, tierRank,
nominalFailureBound, confidence) and the consumer's class standings (nlb:n, nlb:defects), bound
requests (nlb:BoundRequest) and crown thresholds (nlb:CrownThreshold with nlb:yieldLowerBound), and
writes two RDF documents:

  tiers_out   per tier: zeroDefectUpperBound, oneDefectUpperBound, ruleOfThreeBound, minNZeroDefect;
              per yield threshold: minNForLowerBound
  bounds_out  one nlb:BoundRow (boundN, boundDefects, exactUpperBound) per distinct requested (n, x):
              every tier's (N, 0) and (N, 1), every class standing's (n, defects), every request

Bound: exact one-sided Clopper-Pearson upper limit at confidence c (alpha = 1 - c):
  p_U(n, x) = BetaInv(c; x + 1, n - x);  x = 0: 1 - alpha^(1/n);  n = 0 or x >= n: 1.
Computed with the standard library only (log-space binomial CDF + bisection); literals are rounded
to the nearest 6th decimal (half-even), the resolution of every tier table of the design (a claim is
compared with the row at that resolution; the rounding error is below 5e-7). SPARQL 1.1 has no pow/log (ggen
refuses math:pow, FM-GRAPH-003): these rows are data that shapes and gates compare against.

  evidence_tiers.py --consumer DIR          write both outputs
  evidence_tiers.py --consumer DIR --check  exit 0 iff the committed outputs equal a fresh computation,
                                            every row agrees with scipy beta.ppf and statsmodels
                                            proportion_confint(method="beta") to 1e-9, tiers are
                                            strictly ordered (N_discovery < N_qualification <
                                            N_operational < N_scale) and each exact zero-defect bound
                                            is within its nominal tier bound
Exit: 0 ok; 1 REFUSED; 2 usage; 75 UNKNOWN (a cross-check library is absent).
"""
from __future__ import annotations

import argparse
import hashlib
import math
import sys
import tomllib
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

import rdflib
from rdflib.namespace import RDF

NLB = rdflib.Namespace("https://ggen.dev/nonllm-bench#")
XSD_DECIMAL = "http://www.w3.org/2001/XMLSchema#decimal"
SIX = Decimal("0.000001")


def upper_bound(n: int, x: int, confidence: float) -> float:
    """Exact one-sided Clopper-Pearson upper bound for x defects in n trials."""
    if n < 0 or x < 0:
        raise ValueError(f"invalid (n, x) = ({n}, {x})")
    if n == 0 or x >= n:
        return 1.0
    alpha = 1.0 - confidence
    if x == 0:
        return 1.0 - alpha ** (1.0 / n)

    def cdf(p: float) -> float:
        # P(X <= x | n, p) in log space.
        logs = [
            math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
            + k * math.log(p) + (n - k) * math.log1p(-p)
            for k in range(x + 1)
        ]
        top = max(logs)
        return math.exp(top) * sum(math.exp(v - top) for v in logs)

    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if cdf(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def round6(value: float) -> str:
    return str(Decimal(repr(value)).quantize(SIX, rounding=ROUND_HALF_EVEN))


def min_n_zero_defect(alpha: float, nominal: float) -> int:
    return math.ceil(math.log(alpha) / math.log(1.0 - nominal))


def min_n_for_lower_bound(alpha: float, yield_target: float, confidence: float) -> int:
    n = math.ceil(math.log(alpha) / math.log(yield_target))
    # Direct confirmation against the kernel's own bound (guards the closed form).
    while 1.0 - upper_bound(n, 0, confidence) < yield_target:
        n += 1
    while n > 1 and 1.0 - upper_bound(n - 1, 0, confidence) >= yield_target:
        n -= 1
    return n


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Kernel:
    def __init__(self, consumer: Path):
        self.consumer = consumer
        config = tomllib.loads((consumer / "bench.toml").read_text(encoding="utf-8"))["kernel"]
        self.config = config
        self.namespace = config["namespace"]
        self.confidence = float(config["confidence"])
        self.alpha = 1.0 - self.confidence
        self.inputs = [consumer / p for p in config["inputs"]]
        self.graph = rdflib.Graph()
        for path in self.inputs:
            self.graph.parse(path, format="turtle")

    def tiers(self) -> list[dict]:
        g = self.graph
        rows = []
        for tier in g.subjects(RDF.type, NLB.EvidenceTier):
            rows.append({
                "iri": str(tier),
                "rank": int(g.value(tier, NLB.tierRank)),
                "n": int(g.value(tier, NLB.tierN)),
                "nominal": float(g.value(tier, NLB.nominalFailureBound)),
                "confidence": float(g.value(tier, NLB.confidence)),
            })
        rows.sort(key=lambda r: r["rank"])
        return rows

    def requested_pairs(self, tiers: list[dict]) -> list[tuple[int, int]]:
        g = self.graph
        pairs: set[tuple[int, int]] = {(0, 0)}
        for t in tiers:
            if t["n"] > 0:
                pairs.add((t["n"], 0))
                pairs.add((t["n"], 1))
        for s in g.subjects(RDF.type, NLB.ClassStanding):
            n, d = g.value(s, NLB.n), g.value(s, NLB.defects)
            if n is not None and d is not None:
                pairs.add((int(n), int(d)))
        for r in g.subjects(RDF.type, NLB.BoundRequest):
            pairs.add((int(g.value(r, NLB.requestN)), int(g.value(r, NLB.requestDefects))))
        return sorted(pairs)

    def thresholds(self) -> list[tuple[str, float]]:
        g = self.graph
        out = []
        for th in g.subjects(RDF.type, NLB.CrownThreshold):
            if g.value(th, NLB.yieldLowerBound) is not None and bool(g.value(th, NLB.yieldLowerBound).toPython()):
                out.append((str(th), float(g.value(th, NLB.thresholdValue))))
        return sorted(out)

    def header(self, what: str) -> list[str]:
        lines = [
            f"# GENERATED by nonllm-class-qualification-pack scripts/evidence_tiers.py ({what}); do not edit.",
            f"# kernel: scripts/evidence_tiers.py sha256:{sha256_file(Path(__file__).resolve())}",
        ]
        for path in self.inputs:
            lines.append(f"# input: {path.relative_to(self.consumer)} sha256:{sha256_file(path)}")
        lines.append(f"# bound: exact one-sided Clopper-Pearson, confidence {self.config['confidence']}, rounded to 6 decimals (half-even)")
        lines.append("")
        return lines

    def render(self) -> tuple[str, str, list[tuple[int, int, float]]]:
        tiers = self.tiers()
        computed_by = f'"evidence_tiers.py sha256:{sha256_file(Path(__file__).resolve())}"'

        def dec(s: str) -> str:
            return f'"{s}"^^<{XSD_DECIMAL}>'

        t_lines = self.header("tiers and threshold sizes")
        for t in tiers:
            conf = t["confidence"]
            if t["n"] == 0:
                zero, one, r3 = 1.0, 1.0, None
            else:
                zero, one, r3 = upper_bound(t["n"], 0, conf), upper_bound(t["n"], 1, conf), 3.0 / t["n"]
            t_lines.append(f"<{t['iri']}> <{NLB}zeroDefectUpperBound> {dec(round6(zero))} ;")
            t_lines.append(f"    <{NLB}oneDefectUpperBound> {dec(round6(one))} ;")
            if r3 is not None:
                t_lines.append(f"    <{NLB}ruleOfThreeBound> {dec(round6(r3))} ;")
            if 0.0 < t["nominal"] < 1.0:
                t_lines.append(f"    <{NLB}minNZeroDefect> {min_n_zero_defect(1.0 - conf, t['nominal'])} ;")
            t_lines.append(f"    <{NLB}computedBy> {computed_by} .")
        for iri, target in self.thresholds():
            t_lines.append(f"<{iri}> <{NLB}minNForLowerBound> {min_n_for_lower_bound(self.alpha, target, self.confidence)} ;")
            t_lines.append(f"    <{NLB}computedBy> {computed_by} .")
        t_lines.append("")
        b_lines = self.header("exact bound rows")
        rows = []
        for n, x in self.requested_pairs(tiers):
            p = upper_bound(n, x, self.confidence)
            rows.append((n, x, p))
            b_lines.append(f"<{self.namespace}bound-{n}-{x}> a <{NLB}BoundRow> ;")
            b_lines.append(f"    <{NLB}boundN> {n} ;")
            b_lines.append(f"    <{NLB}boundDefects> {x} ;")
            b_lines.append(f"    <{NLB}exactUpperBound> {dec(round6(p))} ;")
            b_lines.append(f"    <{NLB}computedBy> {computed_by} .")
        b_lines.append("")
        return "\n".join(t_lines), "\n".join(b_lines), rows


def check(kernel: Kernel, tiers_text: str, bounds_text: str, rows: list[tuple[int, int, float]]) -> int:
    fails = []
    for rel, text in ((kernel.config["tiers_out"], tiers_text), (kernel.config["bounds_out"], bounds_text)):
        path = kernel.consumer / rel
        if not path.is_file() or path.read_text(encoding="utf-8") != text:
            fails.append(f"REFUSED[kernel_output_drift] {rel} differs from a fresh kernel computation")
    try:
        from scipy.stats import beta  # second implementation (Boost incomplete-beta inverse)
        from statsmodels.stats.proportion import proportion_confint  # third implementation
    except ImportError as exc:
        print(f"UNKNOWN[TOOL_MISSING] cross-check library absent: {exc}")
        return 75
    conf = kernel.confidence
    worst = 0.0
    for n, x, p in rows:
        if n == 0 or x >= n:
            ref_a = ref_b = 1.0
        else:
            ref_a = float(beta.ppf(conf, x + 1, n - x))
            ref_b = float(proportion_confint(x, n, alpha=2 * (1 - conf), method="beta")[1])
        worst = max(worst, abs(p - ref_a), abs(p - ref_b))
        if abs(p - ref_a) > 1e-9 or abs(p - ref_b) > 1e-9:
            fails.append(f"REFUSED[kernel_disagrees] (n={n}, x={x}) kernel {p!r} scipy {ref_a!r} statsmodels {ref_b!r}")
    pinned = {(30, 0): "0.095034", (300, 0): "0.009936"}
    by_pair = {(n, x): round6(p) for n, x, p in rows}
    for pair, want in pinned.items():
        if by_pair.get(pair) != want:
            fails.append(f"REFUSED[kernel_pin] (n={pair[0]}, x={pair[1]}) bound {by_pair.get(pair)} != {want}")
    tiers = [t for t in kernel.tiers() if t["n"] > 0]
    for a, b in zip(tiers, tiers[1:]):
        if not (a["n"] < b["n"]):
            fails.append(f"REFUSED[tier_order] N {a['n']} (rank {a['rank']}) is not below N {b['n']} (rank {b['rank']})")
    for t in tiers:
        zero = upper_bound(t["n"], 0, t["confidence"])
        if zero > t["nominal"]:
            fails.append(f"REFUSED[tier_bound] tier N={t['n']} exact zero-defect bound {zero:.6f} exceeds its nominal {t['nominal']}")
    for line in fails:
        print(line)
    if fails:
        return 1
    print(f"KERNEL OK: {len(rows)} bound rows, {len(tiers)} tiers strictly ordered "
          f"({' < '.join(str(t['n']) for t in tiers)}), max |kernel - scipy/statsmodels| = {worst:.3e}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--consumer", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    kernel = Kernel(args.consumer.resolve())
    tiers_text, bounds_text, rows = kernel.render()
    if args.check:
        return check(kernel, tiers_text, bounds_text, rows)
    for rel, text in ((kernel.config["tiers_out"], tiers_text), (kernel.config["bounds_out"], bounds_text)):
        path = kernel.consumer / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"KERNEL WROTE {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
