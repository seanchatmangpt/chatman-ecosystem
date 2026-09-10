#!/usr/bin/env python3
"""Verify fleet scope plus typed release-candidate / observation separation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
RECEIPT_SCHEMA = "chatman.portfolio-verification/3"
DISPOSITION_KEYS = {
    "crown": "CROWN", "required": "REQUIRED", "adapter": "ADAPTER",
    "bench_gym": "BENCH_GYM", "source_archaeology": "SOURCE_ARCHAEOLOGY",
    "explicit_out_of_release": "OUT_OF_RELEASE",
}
ALLOWED_SCOPE_STANDINGS = {"UNKNOWN", "PARTIAL_ALIVE", "ALIVE", "BLOCKED", "BUILD_BROKEN", "UNSUPPORTED"}

class PortfolioRefusal(ValueError): pass

def load(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle: return tomllib.load(handle)

def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")

def digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()

def input_digests(policy: dict[str, Any], manifest: dict[str, Any], ledger: dict[str, Any]) -> dict[str, str]:
    """Measure exact semantic inputs so a valid old receipt cannot certify new state."""
    return {"fleet": digest(policy), "manifest": digest(manifest), "ledger": digest(ledger)}

def classify(policy: dict[str, Any], repository: str) -> str:
    fleet = policy["fleet"]
    if repository == fleet["composition_root"]: return "CROWN"
    for key, disposition in DISPOSITION_KEYS.items():
        if repository in policy["dispositions"].get(key, []): return disposition
    return fleet["default_disposition"]

def row_kind(row: dict[str, Any]) -> str:
    explicit = row.get("kind")
    inferred = "CANDIDATE" if "candidate_sha" in row else "OBSERVATION"
    if explicit is None: return inferred
    if explicit not in {"CANDIDATE", "OBSERVATION"}: raise PortfolioRefusal(f"REFUSED[LEDGER_KIND_INVALID] {explicit!r}")
    if explicit != inferred: raise PortfolioRefusal(f"REFUSED[LEDGER_KIND_SHAPE_MISMATCH] kind={explicit} inferred={inferred}")
    return explicit

def validate_pagination_evidence(fleet: dict[str, Any]) -> list[dict[str, str]]:
    findings=[]
    def add(code, subject, detail): findings.append({"code":code,"subject":subject,"detail":detail})
    count,pages,page_size,term=(fleet.get("observed_owned_repository_count"),fleet.get("nonempty_pages"),fleet.get("page_size"),fleet.get("next_page_empty"))
    if not isinstance(count,int) or isinstance(count,bool) or count<1: add("FLEET_OBSERVED_COUNT_INVALID","fleet.observed_owned_repository_count",str(count))
    if not isinstance(pages,int) or isinstance(pages,bool) or pages<1: add("FLEET_NONEMPTY_PAGES_INVALID","fleet.nonempty_pages",str(pages))
    if not isinstance(page_size,int) or isinstance(page_size,bool) or page_size<1: add("FLEET_PAGE_SIZE_INVALID","fleet.page_size",str(page_size))
    if term is not True: add("FLEET_PAGINATION_TERMINATOR_INVALID","fleet.next_page_empty",str(term))
    if findings: return findings
    minimum,maximum=(pages-1)*page_size+1,pages*page_size
    if not minimum<=count<=maximum: add("FLEET_OBSERVED_COUNT_PAGINATION_MISMATCH","fleet",f"count={count} requires {minimum}..{maximum} for pages={pages} page_size={page_size}")
    return findings

def validate(policy: dict[str, Any], manifest: dict[str, Any], ledger: dict[str, Any]) -> list[dict[str, str]]:
    findings=[]; fleet=policy.get("fleet",{}); roadmap=policy.get("roadmap",{}); dispositions=policy.get("dispositions",{})
    def add(code,subject,detail): findings.append({"code":code,"subject":subject,"detail":detail})
    if fleet.get("owner")!="seanchatmangpt": add("FLEET_OWNER_INVALID","fleet.owner",str(fleet.get("owner")))
    findings.extend(validate_pagination_evidence(fleet))
    if fleet.get("default_disposition")!="OUT_OF_RELEASE" or fleet.get("default_release_blocking") is not False: add("FLEET_DEFAULT_NOT_FAIL_SAFE","fleet","unclassified repositories must be non-blocking OUT_OF_RELEASE")
    missing=sorted({"CROWN","REQUIRED","ADAPTER","BENCH_GYM","SOURCE_ARCHAEOLOGY","OUT_OF_RELEASE"}-roadmap.keys())
    if missing: add("FLEET_ROADMAP_MISSING","roadmap",",".join(missing))
    seen={}
    for key,disp in DISPOSITION_KEYS.items():
        repos=dispositions.get(key,[])
        if not isinstance(repos,list) or not all(isinstance(r,str) for r in repos): add("FLEET_DISPOSITION_LIST_INVALID",key,"must be an array of repository coordinates"); continue
        for repo in repos:
            if not repo.startswith("seanchatmangpt/"): add("FLEET_REPOSITORY_OWNER_INVALID",repo,key)
            if repo in seen: add("FLEET_REPOSITORY_MULTI_DISPOSITION",repo,f"{seen[repo]} and {disp}")
            seen[repo]=disp
    components=manifest.get("components",[]); expected={c["repository"]:c["disposition"] for c in components if c.get("required")}; actual={r:d for r,d in seen.items() if d in {"CROWN","REQUIRED"}}
    if expected!=actual: add("FLEET_RELEASE_CLOSURE_MISMATCH","dispositions",f"manifest={sorted(expected.items())} fleet={sorted(actual.items())}")
    root=fleet.get("composition_root")
    if not isinstance(root,str) or classify(policy,root)!="CROWN": add("FLEET_COMPOSITION_ROOT_INVALID",str(root),"composition root must classify as CROWN")
    by_component={c["id"]:c for c in components}; seen_components=set()
    for row in ledger.get("candidates",[]):
        cid=row.get("component")
        if cid in seen_components: add("CANDIDATE_DUPLICATE_COMPONENT",str(cid),"one ledger row per component"); continue
        seen_components.add(cid); admitted=by_component.get(cid)
        if admitted is None: add("CANDIDATE_COMPONENT_NOT_ADMITTED",str(cid),"ledger component must exist in release manifest"); continue
        if row.get("repository")!=admitted.get("repository"): add("CANDIDATE_REPOSITORY_MISMATCH",str(cid),str(row.get("repository")))
        if row.get("scope_standing") not in ALLOWED_SCOPE_STANDINGS: add("CANDIDATE_SCOPE_STANDING_INVALID",str(cid),str(row.get("scope_standing")))
        if row.get("release_standing")!="UNKNOWN": add("CANDIDATE_RELEASE_STANDING_OVERCLAIM",str(cid),str(row.get("release_standing")))
        try: kind=row_kind(row)
        except PortfolioRefusal as exc: add("LEDGER_KIND_REFUSED",str(cid),str(exc)); continue
        if kind=="OBSERVATION":
            observed=row.get("admitted_sha")
            if not isinstance(observed,str) or not SHA_RE.fullmatch(observed): add("OBSERVATION_SHA_INVALID",str(cid),str(observed))
            if "exact_head_ci" in row: add("OBSERVATION_CI_AUTHORITY_INVALID",str(cid),str(row.get("exact_head_ci")))
            continue
        if row.get("admitted_sha")!=admitted.get("sha"): add("CANDIDATE_ADMITTED_SHA_MISMATCH",str(cid),f"manifest={admitted.get('sha')} candidate={row.get('admitted_sha')}")
        candidate=row.get("candidate_sha")
        if not isinstance(candidate,str) or not SHA_RE.fullmatch(candidate): add("CANDIDATE_SHA_INVALID",str(cid),str(candidate))
        if candidate==admitted.get("sha"): add("CANDIDATE_NOT_DISTINCT",str(cid),"candidate SHA must remain distinct until promotion")
        if row.get("exact_head_ci")!="SUCCESS": add("CANDIDATE_EXACT_HEAD_CI_NOT_SUCCESS",str(cid),str(row.get("exact_head_ci")))
    return findings

def build_report(policy: dict[str, Any], manifest: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    findings=validate(policy,manifest,ledger); candidates=observations=0
    for row in ledger.get("candidates",[]):
        try: kind=row_kind(row)
        except PortfolioRefusal: continue
        candidates += kind=="CANDIDATE"; observations += kind=="OBSERVATION"
    return {"schema":RECEIPT_SCHEMA,"release":manifest.get("release",{}).get("version"),"input_digests":input_digests(policy,manifest,ledger),"observed_owned_repository_count":policy.get("fleet",{}).get("observed_owned_repository_count"),"default_disposition":policy.get("fleet",{}).get("default_disposition"),"explicit_non_default_repositories":sum(len(policy.get("dispositions",{}).get(k,[])) for k in DISPOSITION_KEYS),"candidate_count":candidates,"observation_count":observations,"standing":"ALIVE" if not findings else "BLOCKED","findings":findings}

def manufacture_receipt(report: dict[str, Any]) -> dict[str, Any]:
    body=dict(report); return {**body,"sha256":digest(body)}

def replay_receipt(receipt: dict[str, Any], expected_inputs: dict[str, str] | None = None) -> dict[str, Any]:
    if receipt.get("schema")!=RECEIPT_SCHEMA: raise PortfolioRefusal("REFUSED[PORTFOLIO_RECEIPT_SCHEMA]")
    value=receipt.get("sha256")
    if not isinstance(value,str) or not DIGEST_RE.fullmatch(value): raise PortfolioRefusal("REFUSED[PORTFOLIO_RECEIPT_DIGEST_INVALID]")
    body={k:v for k,v in receipt.items() if k!="sha256"}
    if digest(body)!=value: raise PortfolioRefusal("REFUSED[PORTFOLIO_RECEIPT_TAMPERED]")
    measured=receipt.get("input_digests")
    if not isinstance(measured,dict) or set(measured)!={"fleet","manifest","ledger"} or not all(isinstance(v,str) and DIGEST_RE.fullmatch(v) for v in measured.values()): raise PortfolioRefusal("REFUSED[PORTFOLIO_INPUT_DIGESTS_INVALID]")
    if expected_inputs is not None and measured!=expected_inputs: raise PortfolioRefusal("REFUSED[PORTFOLIO_RECEIPT_STALE]")
    if receipt.get("standing")!="ALIVE" or receipt.get("findings")!=[]: raise PortfolioRefusal("REFUSED[PORTFOLIO_RECEIPT_NOT_ALIVE]")
    return receipt

def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--fleet",type=Path,default=Path("release/v26.9.1/fleet-policy.toml")); parser.add_argument("--manifest",type=Path,default=Path("release/v26.9.1/manifest.toml")); parser.add_argument("--candidates",type=Path,default=Path("release/v26.9.1/candidates.toml")); parser.add_argument("--receipt",type=Path); parser.add_argument("--replay",type=Path); args=parser.parse_args(argv)
    try:
        policy,manifest,ledger=load(args.fleet),load(args.manifest),load(args.candidates)
        if args.replay:
            receipt=json.loads(args.replay.read_text(encoding="utf-8")); replay_receipt(receipt,input_digests(policy,manifest,ledger)); print(json.dumps(receipt,sort_keys=True)); return 0
        report=build_report(policy,manifest,ledger); receipt=manufacture_receipt(report)
        if args.receipt: args.receipt.write_text(json.dumps(receipt,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps(receipt,indent=2,sort_keys=True)); return 0 if not report["findings"] else 2
    except (OSError,json.JSONDecodeError,PortfolioRefusal) as exc: print(str(exc)); return 2

if __name__=="__main__": sys.exit(main())
