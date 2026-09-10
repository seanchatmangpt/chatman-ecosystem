#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,sys,tomllib
from pathlib import Path
VERSION="26.8.23"; SHA40=re.compile(r"^[0-9a-f]{40}$")
REQ_STATES={"ADMITTED","CANDIDATE","ALIVE","UNKNOWN","UNSUPPORTED","REFUSED","BLOCKED","BUILD_BROKEN"}
STANDING={"UNKNOWN","PARTIAL_ALIVE","ALIVE","BLOCKED","BUILD_BROKEN","UNSUPPORTED"}
class ReleaseRefusal(ValueError): pass
def load(p):
 with p.open("rb") as f:return tomllib.load(f)
def req(ok,code):
 if not ok: raise ReleaseRefusal(f"REFUSED[{code}]")
def dag(rows):
 ids={r["id"] for r in rows}; g={r["id"]:tuple(r.get("depends_on",())) for r in rows}
 for n,ps in g.items(): req(all(p in ids for p in ps),"UNKNOWN_REQUIREMENT_DEPENDENCY")
 visiting=set();done=set()
 def visit(n):
  if n in visiting: raise ReleaseRefusal("REFUSED[REQUIREMENT_CYCLE]")
  if n in done:return
  visiting.add(n)
  for p in g[n]:visit(p)
  visiting.remove(n);done.add(n)
 for n in sorted(g):visit(n)
 return g
def verify(root:Path):
 cargo=load(root/"Cargo.toml"); man=load(root/f"release/v{VERSION}/manifest.toml"); rd=load(root/f"release/v{VERSION}/requirements.toml")
 release=man["release"]; rows=rd.get("requirements",[]); candidates=man.get("candidates",[])
 req(str(cargo["workspace"]["package"]["version"])==VERSION,"WORKSPACE_VERSION_MISMATCH")
 req(str(release.get("version"))==VERSION and str(rd.get("version"))==VERSION,"RELEASE_VERSION_MISMATCH")
 req(release.get("target_date")=="2026-08-23","RELEASE_DATE_MISMATCH")
 req(release.get("base_ref")=="main" and bool(SHA40.fullmatch(str(release.get("base_sha","")))),"INEXACT_BASE")
 req(release.get("standing") in STANDING,"INVALID_RELEASE_STANDING")
 req(release.get("consequential_do")==rd.get("consequential_do")=="BRCE_ONLY","AUTHORITY_WIDENED")
 req(release.get("future_composition_line")=="release/v26.9.1" and (root/"release/v26.9.1").exists(),"FUTURE_LINE_NOT_PRESERVED")
 ids=[r.get("id") for r in rows]; req(len(rows)>=10,"INSUFFICIENT_REQUIREMENT_COVERAGE"); req(len(ids)==len(set(ids)),"DUPLICATE_REQUIREMENT_ID")
 req(all(isinstance(i,str) and i for i in ids),"EMPTY_REQUIREMENT_ID"); req(all(r.get("state") in REQ_STATES for r in rows),"INVALID_REQUIREMENT_STATE")
 req(all(str(r.get("acceptance","")).strip() for r in rows),"MISSING_ACCEPTANCE"); graph=dag(rows)
 cids=[c.get("id") for c in candidates]; req(len(cids)==len(set(cids)),"DUPLICATE_CANDIDATE_ID")
 for c in candidates:
  req(c.get("repository")=="seanchatmangpt/chatman-ecosystem","FOREIGN_CANDIDATE_REPOSITORY"); req(bool(SHA40.fullmatch(str(c.get("sha","")))),"INEXACT_CANDIDATE_SHA"); req(isinstance(c.get("pr"),int) and c["pr"]>0,"INVALID_CANDIDATE_PR")
 unresolved=sorted(r["id"] for r in rows if r["state"]!="ALIVE")
 if release["standing"]=="ALIVE": req(not unresolved,"FALSE_ALIVE_WITH_OPEN_REQUIREMENTS")
 body={"schema":"chatman.release-v26.8.23/1","version":VERSION,"base_sha":release["base_sha"],"workspace_version":VERSION,"standing":release["standing"],"requirement_ids":sorted(ids),"candidate_subjects":sorted(f'{c["id"]}@{c["sha"]}' for c in candidates),"unresolved":unresolved,"authority":release["authority"],"consequential_do":release["consequential_do"],"actuation_performed":False}
 digest=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest(); return {"status":"VERIFIED","receipt_sha256":digest,"body":body,"dependency_graph":graph}
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument("--root",default=".");p.add_argument("--json",action="store_true");ns=p.parse_args(argv)
 try:r=verify(Path(ns.root))
 except (ReleaseRefusal,KeyError,FileNotFoundError,tomllib.TOMLDecodeError) as e: print(str(e),file=sys.stderr);return 2
 print(json.dumps(r,sort_keys=True,separators=(",",":")) if ns.json else f'VERIFIED {r["receipt_sha256"]}');return 0
if __name__=="__main__":raise SystemExit(main())
