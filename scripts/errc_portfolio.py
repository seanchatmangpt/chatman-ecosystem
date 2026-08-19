#!/usr/bin/env python3
"""Manufacture a deterministic 80/20 ERRC portfolio plan; never actuate."""
from __future__ import annotations

import argparse, hashlib, json, math, sys, tomllib
from itertools import combinations
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

D_MAN = Path("release/v26.9.1/manifest.toml")
D_FLEET = Path("release/v26.9.1/fleet-policy.toml")
D_POLICY = Path("release/v26.9.1/errc-policy.toml")
D_SURVEY = Path(".artifacts/portfolio-survey/FINDINGS.json")
D_OUT = Path(".artifacts/portfolio-survey")

class ERRCError(RuntimeError): pass

def toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as f: return tomllib.load(f)

def js(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict): raise ERRCError(f"JSON object required: {path}")
    return value

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()

def digest(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()

def strings(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
        raise ERRCError(f"{name} must be an array of strings")
    return list(value)

def admit(policy: Mapping[str, Any]) -> dict[str, Any]:
    p = policy.get("errc")
    if not isinstance(p, dict): raise ERRCError("[errc] policy required")
    fraction, target, max_prs = p.get("focus_fraction"), p.get("minimum_relief_coverage"), p.get("max_active_prs_per_repository")
    if isinstance(fraction, bool) or not isinstance(fraction, (int,float)) or not 0 < float(fraction) <= 1: raise ERRCError("focus_fraction must be in (0,1]")
    if isinstance(target, bool) or not isinstance(target, (int,float)) or not 0 < float(target) <= 1: raise ERRCError("minimum_relief_coverage must be in (0,1]")
    if isinstance(max_prs, bool) or not isinstance(max_prs, int) or max_prs < 1: raise ERRCError("max_active_prs_per_repository must be >=1")
    if p.get("do_authority") is not False: raise ERRCError("do_authority must be false")
    return {
        "schema": str(p.get("schema", "chatman.errc.80-20.v1")), "fraction": float(fraction), "target": float(target), "max_prs": max_prs,
        "freeze": strings(p.get("freeze_dispositions", []), "freeze_dispositions"),
        "reduce": strings(p.get("reduce_dispositions", []), "reduce_dispositions"),
        "eliminate_prefixes": [x.casefold() for x in strings(p.get("eliminate_pr_title_prefixes", []), "eliminate_pr_title_prefixes")],
        "reduce_prefixes": [x.casefold() for x in strings(p.get("reduce_pr_title_prefixes", []), "reduce_pr_title_prefixes")],
    }

def graph(manifest: Mapping[str, Any]) -> tuple[dict[str,dict[str,Any]],dict[str,list[str]],dict[str,set[str]]]:
    rows = manifest.get("components")
    if not isinstance(rows, list): raise ERRCError("manifest components array required")
    by = {r["id"]: dict(r) for r in rows if isinstance(r,dict) and r.get("required") is True and isinstance(r.get("id"),str)}
    if not by: raise ERRCError("no required components")
    deps: dict[str,list[str]] = {}; rev: dict[str,set[str]] = defaultdict(set)
    for cid,row in by.items():
        ds = row.get("depends_on", [])
        if not isinstance(ds,list) or any(d not in by for d in ds): raise ERRCError(f"invalid dependency closure: {cid}")
        deps[cid] = list(ds)
        for d in ds: rev[d].add(cid)
    visiting:set[str]=set(); done:set[str]=set()
    def visit(n:str)->None:
        if n in visiting: raise ERRCError(f"dependency cycle at {n}")
        if n in done: return
        visiting.add(n)
        for d in deps[n]: visit(d)
        visiting.remove(n); done.add(n)
    for n in sorted(by): visit(n)
    return by,deps,rev

def closure(rev: Mapping[str,set[str]], start: str) -> set[str]:
    seen={start}; stack=list(rev.get(start,set()))
    while stack:
        n=stack.pop()
        if n in seen: continue
        seen.add(n); stack.extend(rev.get(n,set()))
    return seen

def focus(manifest: Mapping[str,Any], policy: Mapping[str,Any]) -> dict[str,Any]:
    p=admit(policy); by,deps,_=graph(manifest); unresolved={n for n,r in by.items() if r.get("standing") != "ALIVE"}
    budget=max(1, math.ceil(len(by)*p["fraction"]))
    if not unresolved: return {"required":len(by),"unresolved":0,"budget":budget,"selected":[],"coverage":1.0,"covered":[],"uncovered":[],"target_met":True}
    ready={n for n in unresolved if all(by[d].get("standing") == "ALIVE" for d in deps[n])}
    if not ready: raise ERRCError("no dependency-ready unresolved component")
    memo:dict[str,set[str]]={}
    def blockers(n:str)->set[str]:
        if n in memo: return memo[n]
        if n in ready: result={n}
        else:
            result=set()
            for d in deps[n]:
                if d in unresolved: result |= blockers(d)
        memo[n]=result; return result
    blocker_sets={n:blockers(n) for n in unresolved}
    roots=sorted(ready); max_k=min(budget,len(roots)); best:tuple[str,...]=(); best_covered:set[str]=set()
    for k in range(1,max_k+1):
        for candidate in combinations(roots,k):
            chosen=set(candidate); covered={n for n,b in blocker_sets.items() if b <= chosen}
            score=(len(covered), -len(candidate), tuple(candidate))
            best_score=(len(best_covered), -len(best), tuple(best))
            if score > best_score: best=candidate; best_covered=covered
    ordered=[]; chosen:set[str]=set(); previous:set[str]=set(); remaining=set(best)
    while remaining:
        ranked=[]
        for root in remaining:
            c=chosen|{root}; now={n for n,b in blocker_sets.items() if b <= c}; marginal=now-previous
            ranked.append((len(marginal),root,now,marginal))
        ranked.sort(key=lambda x:(-x[0],x[1])); _,root,now,marginal=ranked[0]; remaining.remove(root); chosen.add(root); previous=now
        r=by[root]; ordered.append({"component":root,"repository":r.get("repository"),"role":r.get("role"),"standing":r.get("standing","UNKNOWN"),"potential_relief":len({n for n,b in blocker_sets.items() if root in b}),"marginal_relief":len(marginal),"marginal_components":sorted(marginal)})
    coverage=len(best_covered)/len(unresolved)
    return {"required":len(by),"unresolved":len(unresolved),"budget":budget,"selected":ordered,"coverage":round(coverage,6),"covered":sorted(best_covered),"uncovered":sorted(unresolved-best_covered),"target_met":coverage>=p["target"],"selection":"EXHAUSTIVE_READY_ROOT_COMBINATIONS"}

def starts(title: str, prefixes: list[str]) -> bool:
    t=title.casefold().strip(); return any(t.startswith(p) for p in prefixes)

def build(manifest: Mapping[str,Any], fleet: Mapping[str,Any], survey: Mapping[str,Any], policy: Mapping[str,Any]) -> dict[str,Any]:
    p=admit(policy); f=focus(manifest,policy); actions={k:[] for k in ("ELIMINATE","REDUCE","RAISE","CREATE")}
    repos=survey.get("repositories",[]); prs=survey.get("open_core_prs",[])
    if not isinstance(repos,list) or not isinstance(prs,list): raise ERRCError("survey arrays required")
    counts=Counter(str(r.get("fleet_disposition","OUT_OF_RELEASE")) for r in repos if isinstance(r,dict))
    frozen=sum(counts[x] for x in p["freeze"]); reduced=sum(counts[x] for x in p["reduce"])
    if frozen: actions["ELIMINATE"].append({"subject":"release-active-wip","count":frozen,"physical_delete":False,"action":"Freeze OUT_OF_RELEASE work; preserve history; re-admit only by dependency evidence."})
    if reduced: actions["REDUCE"].append({"subject":"support-repository-wip","count":reduced,"action":"Pull adapters/gyms/archaeology only from a named required dependency; no parallel release crown."})
    by_repo:dict[str,list[dict[str,Any]]]=defaultdict(list)
    for row in prs:
        if not isinstance(row,dict): continue
        repo=str(row.get("repository","")); by_repo[repo].append(row); subject=f"{repo}#{row.get('number','')}"; title=str(row.get("title",""))
        if starts(title,p["eliminate_prefixes"]): actions["ELIMINATE"].append({"subject":subject,"physical_close":False,"action":"Remove topology-only merge alias from active execution after its canonical successor is admitted; retain provenance."})
        elif starts(title,p["reduce_prefixes"]): actions["REDUCE"].append({"subject":subject,"physical_close":False,"action":"Collapse repeated release doctrine into canonical root/template; keep only repository-specific delta."})
    for repo,rows in sorted(by_repo.items()):
        excess=max(0,len(rows)-p["max_prs"])
        if excess: actions["REDUCE"].append({"subject":repo,"observed_open_prs":len(rows),"target_active_prs":p["max_prs"],"potential_wip_reduction":excess,"action":"Use one active integration/crown surface; preserve other PRs as topology until reconciled."})
    for row in f["selected"]: actions["RAISE"].append({**row,"action":"Raise this dependency-ready high-relief subject first through exact-head verifier, negative fixtures, receipt and replay."})
    actions["CREATE"].append({"subject":"portfolio-errc-control-plane","do_authority":False,"action":"Create one deterministic ERRC projection/receipt instead of leaf-specific prioritizers."})
    total=sum(map(len,by_repo.values())); target=sum(min(len(v),p["max_prs"]) for v in by_repo.values()); summary=survey.get("summary",{}) if isinstance(survey.get("summary",{}),dict) else {}
    release=manifest.get("release",{}) if isinstance(manifest.get("release",{}),dict) else {}; fleet_table=fleet.get("fleet",{}) if isinstance(fleet.get("fleet",{}),dict) else {}
    plan={"schema":p["schema"],"release":release.get("version"),"survey_observed_at":survey.get("observed_at"),"owner":survey.get("owner",fleet_table.get("owner")),
          "observation":{"inventory_mode":summary.get("inventory_mode"),"inventory_complete":summary.get("inventory_complete"),"inventory_standing":summary.get("inventory_standing")},
          "authority":{"phase":"SELECT_CONSTRUCT_ONLY","do_authority":False,"release_standing_mutation":False,"pr_close_mutation":False,"repository_delete_mutation":False},
          "policy":{"focus_fraction":p["fraction"],"minimum_relief_coverage":p["target"],"max_active_prs_per_repository":p["max_prs"]},"focus_frontier":f,
          "wip":{"observed_open_core_prs":total,"repositories_with_open_core_prs":len(by_repo),"target_active_core_prs":target,"potential_parallel_pr_reduction":max(0,total-target)},
          "actions":actions,"standing":"ALIVE" if f["target_met"] else "PARTIAL_ALIVE","standing_scope":"ERRC_PLAN_MANUFACTURE_ONLY","release_standing":"UNCHANGED",
          "falsifiers":["focus contains a subject with unresolved dependency","focus exceeds fraction-derived budget","relief differs from release graph","ERRC performs DO","byte-identical inputs change plan"]}
    plan["plan_digest_sha256"]=digest(plan); return plan

def markdown(plan: Mapping[str,Any]) -> str:
    f=plan["focus_frontier"]; w=plan["wip"]
    lines=["# 80/20 ERRC portfolio plan","",f"Release: `{plan.get('release')}`  ",f"Survey: `{plan.get('survey_observed_at')}`  ",f"Plan digest: `{plan.get('plan_digest_sha256')}`","","SELECT/CONSTRUCT projection only; no merge, close, delete, release, spend, credential use, or external DO.","","## Focus frontier","",f"- required: **{f['required']}**; unresolved: **{f['unresolved']}**; budget: **{f['budget']}**",f"- potential unresolved downstream relief coverage: **{f['coverage']:.1%}**; target met: **{str(f['target_met']).lower()}**","","| # | Component | Standing | Marginal | Potential |","|---:|---|---|---:|---:|"]
    for i,r in enumerate(f["selected"],1): lines.append(f"| {i} | `{r['component']}` | `{r['standing']}` | {r['marginal_relief']} | {r['potential_relief']} |")
    lines += ["","## WIP", "", f"Observed core PRs **{w['observed_open_core_prs']}** → one-surface target **{w['target_active_core_prs']}**; potential parallel-WIP reduction **{w['potential_parallel_pr_reduction']}**.",""]
    for lane in ("ELIMINATE","REDUCE","RAISE","CREATE"):
        lines += [f"## {lane}",""]
        rows=plan["actions"][lane]
        lines += [f"- `{r['subject']}` — {r['action']}" for r in rows] or ["No admitted action."]
        lines.append("")
    lines += ["## Standing","",f"`{plan['standing']}` for `{plan['standing_scope']}`; release standing `{plan['release_standing']}`.","","Relief coverage is topology, not transferred ALIVE standing.",""]
    return "\n".join(lines)

def write(plan: Mapping[str,Any], out: Path)->None:
    out.mkdir(parents=True,exist_ok=True); (out/"ERRC.json").write_text(json.dumps(plan,indent=2,sort_keys=True)+"\n"); (out/"ERRC.md").write_text(markdown(plan))
    sums=[]
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="SHA256SUMS": sums.append(f"{sha(p)}  {p.name}")
    (out/"SHA256SUMS").write_text("\n".join(sums)+"\n")

def main(argv=None)->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--manifest",type=Path,default=D_MAN); ap.add_argument("--fleet",type=Path,default=D_FLEET); ap.add_argument("--policy",type=Path,default=D_POLICY); ap.add_argument("--survey",type=Path,default=D_SURVEY); ap.add_argument("--output-dir",type=Path,default=D_OUT); ap.add_argument("--require-target",action="store_true"); a=ap.parse_args(argv)
    try:
        plan=build(toml(a.manifest),toml(a.fleet),js(a.survey),toml(a.policy)); plan["receipt"]={"schema":"chatman.errc.receipt.v1","manifest_sha256":sha(a.manifest),"fleet_sha256":sha(a.fleet),"policy_sha256":sha(a.policy),"survey_sha256":sha(a.survey),"plan_digest_sha256":plan["plan_digest_sha256"],"replay":"REGENERATE_AND_COMPARE_PLAN_DIGEST","do_authority":False}; write(plan,a.output_dir)
    except (OSError,ValueError,tomllib.TOMLDecodeError,ERRCError) as e:
        print(json.dumps({"standing":"REFUSED:ERRC_ADMISSION","error":str(e)},indent=2),file=sys.stderr); return 2
    print(json.dumps({"standing":plan["standing"],"scope":plan["standing_scope"],"focus":[x["component"] for x in plan["focus_frontier"]["selected"]],"relief_coverage":plan["focus_frontier"]["coverage"],"potential_parallel_pr_reduction":plan["wip"]["potential_parallel_pr_reduction"],"plan_digest_sha256":plan["plan_digest_sha256"],"do_authority":False},indent=2,sort_keys=True))
    return 2 if a.require_target and not plan["focus_frontier"]["target_met"] else 0

if __name__ == "__main__": sys.exit(main())
