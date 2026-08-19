#!/usr/bin/env python3
from pathlib import Path
import re, shutil

FOCUS = {
"foundations": ("the constitutional distinction between knowledge, manufacture, authority, consequence, and standing", r"A=\mu(O^*),\ R=\operatorname{receipt}(A)"),
"algebra": ("the typed algebra separating objects, morphisms, admission, authority, actuation, receipts, and replay", r"\mathrm{SELECT}\neq\mathrm{CONSTRUCT}\neq\mathrm{DO}"),
"geometry": ("admitted-world geometry, authority fibers, causal reachability, and consequence trajectories", r"\gamma:[0,1]\to\mathfrak{W}"),
"information": ("the information budget needed to distinguish apparent outcomes from evidence-backed consequences", r"\Delta I=I(C;E_{new}\mid E_{old})"),
"cryptography": ("cryptographic binding of identity, provenance, semantics, authority, causality, consequence, and replay", r"\mathrm{crypto\ integrity}\neq\mathrm{semantic\ standing}"),
"do": ("the terminality calculus for consequential state transitions", r"\mathrm{ACTUATED}\neq\mathrm{DONE}"),
"brce": ("bounded receipted consequential execution", r"\mathrm{PREPARE}\prec\mathrm{DO}\prec\mathrm{OUTCOME}"),
"autonomy": ("autonomous continuation without human, model, planner, or transport-created authority", r"\mathrm{origin}\not\Rightarrow\mathrm{authority}"),
"standing": ("typed epistemic and operational standing rather than confidence", r"\mathrm{UNKNOWN}\neq\mathrm{ALIVE}"),
"verification": ("claim-bound verification against exact subjects and environments", r"\mathrm{inspection}\neq\mathrm{execution}"),
"dfcm": ("maximal reversible construction before irreversible selection", r"\max|\mathcal{R}|"),
"ontology": ("semantic identity, public ontology reuse, explicit equivalence, and generated projections", r"\mathrm{projection}\neq\mathrm{source\ authority}"),
"process": ("causal partial orders and execution-history geometry", r"P=(V,\prec)"),
"receipts": ("receipt ancestry, durable evidence, replay identity, and drift-sensitive re-admission", r"R_{child}\to R_{parent}"),
"machine-native": ("machine-checkable proof worlds without a natural-language comprehension requirement", r"C_V(P)\le B_V"),
"security": ("non-reachability of unauthorized consequence", r"J^+(d)\subseteq\mathcal{C}_A"),
"castle": ("CASTLE as a reference witness for CONSTRUCT != DO and receipt-bound authority", r"\mathrm{CONSTRUCT}\neq\mathrm{DO}"),
"ggen": ("semantic manufacture from canonical knowledge into independently admitted projections", r"\mathrm{graph}\to\mathrm{ggen}\to\mathrm{admission}"),
"runtime": ("a minimal kernel separating observation, admission, construction, actuation, evidence, and replay", r"O\to O^*\to\mu\to DO\to R"),
"protocols": ("transport-normalized intent with no protocol-created authority", r"\mathrm{transport}\not\Rightarrow\mathrm{authority}"),
"distributed": ("distributed authority, monotonic receipts, and consequence reconciliation", r"R_i\preceq R_{i+1}"),
"failure": ("typed failure, uncertainty-preserving recovery, and consequence-aware retry", r"\mathrm{UNKNOWN}\to\mathrm{OBSERVE}"),
"formal": ("machine-checkable theorem schemas for authority separation, receipt closure, and DO safety", r"\vdash\mathrm{admitted}(d)\Rightarrow\mathrm{bounded}(d)"),
"implementation": ("an implementation architecture preserving the formal authority boundaries", r"\mathrm{candidate}\to\mathrm{admission}\to\mathrm{actuator}"),
"testing": ("tests that attack exact consequential claims and refusal boundaries", r"\mathrm{test}(c)\cap\mathrm{boundary}(c)\neq\varnothing"),
"qualification": ("exact-subject operational qualification", r"\mathrm{ALIVE}\Rightarrow\mathrm{observed\ execution}"),
"post-agi": ("machine-native systems independent of human or LLM comprehension", r"\mathrm{comprehension}\notin\mathrm{admission}(d)"),
"exclusions": ("explicit non-claims and falsifiers preventing obscurity or self-certification", r"\mathrm{falsifier}(c)\neq\varnothing"),
"reference": ("normative vocabulary and schemas for precise replayable claims", r"\mathrm{schema}\to\mathrm{typed\ object}"),
"appendices": ("worked derivations connecting the calculus to receipted execution", r"O\to O^*\to\mu\to DO\to R"),
}

def specific(title):
    t=title.lower()
    if "unknown" in t: return ("uncertainty must remain information rather than becoming approval", r"\mathrm{UNKNOWN}\neq\mathrm{ADMITTED}")
    if "authority" in t: return ("authority is exact and cannot be inferred from intelligence, access, role, or intent", r"\mathrm{capability}\neq\mathrm{authority}")
    if "receipt" in t: return ("receipts bind consequence to ancestry, identity, authority, evidence, and replay", r"R_c\to R_p")
    if "replay" in t: return ("prior success never grants current replay authority after drift", r"\mathrm{prior\ success}\not\Rightarrow\mathrm{replay}")
    if "human" in t: return ("human input is an intent surface, not a privileged oracle", r"\mathrm{human}\not\Rightarrow\mathrm{authority}")
    if any(k in t for k in ("llm","model","agent","planner")): return ("intelligence may construct candidates but does not create consequential authority", r"\mathrm{inference}\not\Rightarrow\mathrm{DO}")
    if any(k in t for k in ("crypto","blake3","signature","post-quantum")): return ("established cryptographic primitives bind bytes while HDITC binds semantic standing", r"\mathrm{integrity}\neq\mathrm{standing}")
    if any(k in t for k in ("do","actuat","consequence")): return ("completion is an observed reconciled consequence, not actuator acknowledgement", r"\mathrm{ACTUATED}\neq\mathrm{DONE}")
    if any(k in t for k in ("verify","test","qualif")): return ("verification must intersect the claim boundary", r"\mathrm{inspection}\neq\mathrm{execution}")
    if any(k in t for k in ("failure","refus","threat","attack")): return ("refusal and failure remain typed outcomes", r"\mathrm{REFUSED}_\tau\neq\mathrm{UNKNOWN}")
    if any(k in t for k in ("ontology","semantic","projection")): return ("meaning is versioned and equivalence requires evidence", r"x\equiv y\Rightarrow\operatorname{proof}(x\sim y)")
    return ("the object remains typed, composable, admission-aware, and unable to create authority by naming itself", r"\mathrm{name}(x)\not\Rightarrow\mathrm{standing}(x)")

def chapter(title, path, part):
    domain=path.split("/",1)[0]
    focus,eq=FOCUS.get(domain,("the HDITC constitutional calculus",r"A=\mu(O^*)"))
    claim,local=specific(title)
    return f"""# {title}

**{title}** develops {focus} within **{part}**. HDITC is a proposed architecture for semantic and consequential standing; dimensionality, opacity, or cognitive difficulty is never itself a cryptographic hardness assumption.

## Law

The local rule is that {claim}:

\\[
{local}
\\]

It composes with the constitutional spine

\\[
A=\\mu(O^*),\\qquad R=\\operatorname{{receipt}}(A),\\qquad {eq}.
\\]

Identity, semantics, authority, bounds, evidence, and receipt ancestry must align at every composition boundary. Successful generation, prediction, compilation, test execution, human approval, or protocol access cannot manufacture a missing authority edge.

## Hyperdimensional interpretation

The admitted world is modeled as \\(\\mathfrak{{W}}\\). Consequential action follows a trajectory \\(\\gamma\\) that must stay within an authority-defined viability region, while its causal future must remain inside the admitted consequence cone:

\\[
\\gamma([0,1])\\subseteq\\mathcal{{V}}_A,
\\qquad
J^+(\\gamma)\\subseteq\\mathcal{{C}}_A.
\\]

Evidence is selected for conditional information gain about the exact claim. A natural-language explanation is only a projection of the proof world; machine verification may validly operate over structures too large or high-dimensional for a human or LLM to reconstruct.

## DO consequence

```text
O -> O* -> CONSTRUCT -> ADMIT
  -> BRCE PREPARE -> DO
  -> OBSERVE -> RECONCILE
  -> BRCE OUTCOME -> RECEIPT -> REPLAY
```

`ACTUATED != DONE`. `DONE` means the exact admitted consequence has closed standing: observed, reconciled, receipted, durable, replay-qualified, and free of unresolved critical `UNKNOWN`.

## Falsifier

The claim loses standing if another subject can reuse its evidence without re-admission; if human, model, planner, transport, or prior success bypasses authority; if actuator acknowledgement becomes `ALIVE` without consequence observation; if contradiction is silently collapsed; or if the receipt cannot bind subject, authority, process, consequence, and ancestry.

The operational question is therefore not whether the system can explain itself, but whether the exact claim can be independently re-verified from admitted objects and receipts.
"""

def main():
    repo=Path(__file__).resolve().parents[1]
    root=repo/"books"/"hditc"
    src=root/"src"
    spec_parts=sorted(root.glob("SUMMARY.spec.*.md"))
    if src.exists(): shutil.rmtree(src)
    src.mkdir(parents=True)
    text="".join(p.read_text() for p in spec_parts)
    (src/"SUMMARY.md").write_text(text)
    (src/"README.md").write_text("""# HDITC

**Hyperdimensional Information-Theoretic Cryptography (HDITC)** is a research architecture for post-AGI consequential systems.

Its thesis is that the evidence required to authorize, execute, observe, and replay consequential transitions can be represented as machine-native semantic objects whose validity is mechanically checkable even when no human or language model can comprehend the complete proof world.

\\[
A=\\mu(O^*),\\qquad R=\\operatorname{receipt}(A)
\\]

and `SELECT != CONSTRUCT != DO`.

HDITC is a proposed doctrine and formalization program. It reuses established cryptographic primitives rather than claiming that cognitive opacity or high dimensionality is itself security. Concrete security claims require implementation-specific threat modeling, cryptanalysis, and verification.
""")
    part="HDITC"
    for line in text.splitlines():
        if line.startswith("# Part "): part=line[2:].strip(); continue
        m=re.match(r"- \[([^\]]+)\]\(([^)]+\.md)\)", line)
        if not m: continue
        title,path=m.groups()
        if path in ("README.md","misc/contributors.md","misc/license.md"): continue
        p=src/path; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(chapter(title,path,part))
    (src/"misc").mkdir(exist_ok=True)
    (src/"misc/contributors.md").write_text("# Contributors\n\nHDITC is authored as part of the Chatman Ecosystem research corpus. Contributions should preserve observation, admission, construction, authority, actuation, receipt, replay, and standing as distinct objects.\n")
    (src/"misc/license.md").write_text("# License\n\nThis book follows the containing repository license unless an explicit book-specific license supersedes it. Third-party standards, ontologies, trademarks, and cryptographic primitives retain their own licenses and authorities.\n")
    (root/"book.toml").write_text("""[book]
title = "HDITC: Hyperdimensional Information-Theoretic Cryptography"
authors = ["Sean Chatman"]
description = "Post-AGI algebra, geometry, information theory, cryptographic standing, and autonomous DO."
language = "en"
src = "src"

[build]
build-dir = "book"
create-missing = false

[output.html]
default-theme = "navy"
preferred-dark-theme = "navy"
mathjax-support = true
no-section-label = true
""")
    links=re.findall(r"\[[^\]]+\]\(([^)]+\.md)\)",(src/"SUMMARY.md").read_text())
    missing=[p for p in links if not (src/p).is_file()]
    empty=[str(p) for p in src.rglob("*.md") if not p.read_text().strip()]
    if missing or empty: raise SystemExit(f"invalid: missing={missing}, empty={empty}")
    print(f"HDITC: {len(list(src.rglob('*.md')))} Markdown files; {len(links)} links; 0 missing; 0 empty")

if __name__=="__main__":
    main()
