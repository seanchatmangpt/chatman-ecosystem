#!/usr/bin/env python3
"""Build the CE23-12 extraction JSON (the LLM edge's raw O) for prose_spans.py emit.

Scratch helper: it only writes the extraction list; binding to byte spans and the
Turtle projection are done by xaas scripts/sjira/prose_spans.py (copied, sha256 86a0e9b3...).
Every quote is checked to occur in the source bytes before writing.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "sjira"  # the CE23-12 prose sources (chatman-ce23-12-*.md)
OUT = Path(__file__).resolve().parents[1] / "candidates"

LM = "LastMile"   # v26.9.23 CE23-12 design (release crown, last mile)
SU = "Successor"  # NON_LLM_OPERATIONAL successor

BENCH = [
    # (kind, statement, quote, required_by, boundary)
    ("Invariant", "A single successful no-LLM episode does not establish that non-LLM feature completion is operational as a class.",
     "The existing no-LLM episode is necessary but not sufficient.", "CE23-12", LM),
    ("Metric", "Class transfer to unseen members is the critical CTQ of the benchmark.",
     "The critical point is **class transfer**. Otherwise we have memorized a fixture.", "CE23-12", LM),
    ("Postcondition", "The DEFINE phase names exactly which work classes are claimed KNOWN and non-LLM.",
     "Define exactly which work classes are claimed KNOWN/non-LLM", "CE23-12", LM),
    ("Postcondition", "The MEASURE phase instruments every transition with OCEL events and receipts.",
     "Instrument every transition using OCEL + receipts", "CE23-12", LM),
    ("Object", "The CTQ tree lists fifteen critical-to-quality characteristics with operational measures and required results.",
     "The DfLSS **Critical-to-Quality** characteristics should be:", "CE23-12", LM),
    ("Evidence", "The golden corpus B1 holds many genuinely known transformations per class, not one fixture.",
     "Build a corpus of genuinely known transformations, not one fixture.", "CE23-12", LM),
    ("Falsifier", "A deterministic worker that accepts invalid work is worse than routing it UNKNOWN (B2 false-accept = 0).",
     "A deterministic worker that “always succeeds” is worse than UNKNOWN.", "CE23-12", LM),
    ("Postcondition", "Variation robustness (B3) is measured with a designed experiment over controlled factors.",
     "Run a designed experiment rather than random chaos.", "CE23-12", LM),
    ("Postcondition", "Every morphism edge failure (B4) ends in a typed state, never uncontrolled continuation.",
     "not uncontrolled continuation.", "CE23-12", LM),
    ("Postcondition", "Unseen-member transfer (B5) freezes class machinery built from training members before execution on unseen instances.",
     "Build class machinery from training/known examples.", "CE23-12", LM),
    ("Invariant", "Near-neighbour non-members (B6) must route UNKNOWN; the admission boundary is measured.",
     "A non-LLM system is only safe if it knows when **not** to apply the known machinery.", "CE23-12", LM),
    ("Metric", "The false-KNOWN admission rate is a safety-critical CTQ.",
     "The latter should be treated as a safety-critical CTQ.", "CE23-12", LM),
    ("Metric", "Rolled throughput yield across stages, not a single success rate, is reported.",
     "So the end-to-end capability is substantially weaker than the individual components appear.", "CE23-12", LM),
    ("Metric", "Cpk is used only where meaningful; discrete correctness uses binomial defect measures.",
     "Use \\(C_{pk}\\) where meaningful, and binomial defect measures for discrete correctness.", "CE23-12", LM),
    ("Transition", "After qualification, statistical process control monitors drift and a special cause triggers standing requalification.",
     "rather than silently assuming ALIVE forever.", None, SU),
    ("Metric", "The first-crown thresholds are initial engineering thresholds, later replaced by control limits from the observed process.",
     "Those are **initial engineering thresholds**, not timeless laws.", "CE23-12", LM),
    ("Exclusion", "The benchmark is not a hand-written suite.",
     "Do not make this another hand-written benchmark suite.", "CE23-12", LM),
    ("Invariant", "Benchmark definitions, case generators, reports and the CI matrix are projections of canonical RDF.",
     "The benchmark definitions, case generators, reports, and CI matrix should be projections.", "CE23-12", LM),
    ("Successor", "Once a class is qualified and SPC-controlled, the LLM is no longer used to solve its members.",
     "Once a class reaches that state, **the LLM should no longer be used to solve members of that class**.", None, SU),
]

STAND = [
    ("Invariant", "CE23-12 benchmark design may ship in v26.9.23 but does not promote operational non-LLM feature completion to ALIVE.",
     "cannot be promoted to ALIVE merely because the benchmark architecture exists.", "CE23-12", LM),
    ("Evidence", "Class-level operational standing comes only from executed benchmark receipts.",
     "actual class-level operational standing must come from executed benchmark receipts.", "CE23-12", LM),
    ("State", "BENCHMARK_DESIGN_ALIVE may be part of v26.9.23.",
     "This can be part of **v26.9.23**.", "CE23-12", LM),
    ("Postcondition", "D: claimed KNOWN classes and CTQs are defined.",
     "claimed KNOWN classes and CTQs defined;", "CE23-12", LM),
    ("Postcondition", "M: the measurement, receipt and OCEL model is defined.",
     "measurement/receipt/OCEL model defined;", "CE23-12", LM),
    ("Postcondition", "A: experiment, DOE, corpus, statistics and qualification rules are defined.",
     "experiment, DOE, corpus, statistics and qualification rules defined.", "CE23-12", LM),
    ("Postcondition", "The benchmark ontology is admitted.", "benchmark ontology admitted", "CE23-12", LM),
    ("Postcondition", "Candidate classes are enumerated.", "candidate classes enumerated", "CE23-12", LM),
    ("Postcondition", "Membership tests are identified for every candidate class.", "membership tests identified", "CE23-12", LM),
    ("Postcondition", "Independent verifiers are identified for every candidate class.", "independent verifiers identified", "CE23-12", LM),
    ("Postcondition", "Near-miss UNKNOWN falsifiers are identified for every candidate class.", "near-miss/UNKNOWN falsifiers identified", "CE23-12", LM),
    ("Postcondition", "The DOE support matrix is generated.", "DOE support matrix generated", "CE23-12", LM),
    ("Postcondition", "The statistical acceptance rules are generated.", "statistical acceptance rules generated", "CE23-12", LM),
    ("Postcondition", "The benchmark work orders are generated.", "benchmark work orders generated", "CE23-12", LM),
    ("Postcondition", "Every generated artifact traces to operator prose.", "all generated artifacts trace to operator prose", "CE23-12", LM),
    ("Invariant", "NON_LLM_OPERATIONAL_ALIVE cannot be established until the generated executor runs the test corpus.",
     "and cannot be established until the generated executor actually runs the test corpus.", "CE23-12", LM),
    ("Invariant", "Documentation about execution is not execution; design standing never implies operational standing.",
     "treating documentation about execution as execution.", "CE23-12", LM),
    ("Metric", "Standing is typed by evidence volume and confidence rather than collapsed into ALIVE.",
     "It means the ontology should encode **confidence and evidence volume**, rather than collapsing everything into ALIVE.", "CE23-12", LM),
    ("Exclusion", "No cross-platform evidence is synthesized.",
     "Do not synthesize fake cross-platform evidence.", "CE23-12", LM),
    ("Postcondition", "The DOE is reduced over the supported factors; OS is not silently treated as invariant.",
     "and the DOE should reduce the design over the supported factors rather than silently treating OS as invariant.", "CE23-12", LM),
    ("Evidence", "The receipt states that cross-OS robustness is outside the demonstrated evidence ceiling.",
     "The receipt should explicitly say that **cross-OS robustness remains outside the demonstrated evidence ceiling**.", "CE23-12", LM),
    ("Postcondition", "The measurement system itself is analysed (MSA) before benchmark results are trusted.",
     "Before trusting benchmark results, test the benchmark itself.", "CE23-12", LM),
    ("Falsifier", "The same artifact receiving different verdicts falsifies MSA repeatability.",
     "Does the same artifact always receive the same verdict?", "CE23-12", LM),
    ("Falsifier", "Disagreement of independent verifiers falsifies MSA classification agreement.",
     "Do independent verifiers agree?", "CE23-12", LM),
    ("Falsifier", "A corrupted output that passes falsifies MSA mutation sensitivity.",
     "Does an intentionally corrupted output reliably fail?", "CE23-12", LM),
    ("Falsifier", "A stale receipt that passes falsifies MSA stale-receipt detection.",
     "Does a stale receipt reliably fail?", "CE23-12", LM),
    ("Falsifier", "An answer that changes with benchmark ordering falsifies MSA ordering invariance.",
     "Can benchmark ordering change the answer?", "CE23-12", LM),
    ("Falsifier", "A classification that changes with cached state falsifies MSA environment reproducibility.",
     "Does cached state change classification?", "CE23-12", LM),
    ("Falsifier", "A near-miss admitted KNOWN by the membership test falsifies the admission boundary.",
     "Can the membership test confuse a near-miss UNKNOWN with KNOWN?", "CE23-12", LM),
    ("Successor", "After v26.9.23 lands, generated benchmark work orders promote specific KNOWN classes from implemented to operationally qualified.",
     "once v26.9.23 lands, the generated benchmark work orders provide the evidence needed", None, SU),
]


def build(src: Path, rows):
    text = src.read_bytes()
    out = []
    for kind, stmt, quote, req, bc in rows:
        n = text.count(quote.encode("utf-8"))
        if n != 1:
            sys.exit(f"quote occurs {n} times in {src.name}: {quote!r}")
        item = {"kind": kind, "statement": stmt, "quote": quote, "boundary_class": bc}
        if req:
            item["required_by"] = req
        out.append(item)
    return out


OUT.mkdir(parents=True, exist_ok=True)
for name, rows in (("chatman-ce23-12-bench", BENCH), ("chatman-ce23-12-standings", STAND)):
    items = build(ROOT / f"{name}.md", rows)
    (OUT / f"{name}.extract.json").write_text(json.dumps(items, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(name, len(items))
