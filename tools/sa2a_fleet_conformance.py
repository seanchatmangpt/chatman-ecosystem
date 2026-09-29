#!/usr/bin/env python3
"""Fail-closed SA2A fleet migration vector verifier."""
import argparse,hashlib,json
from pathlib import Path
REQ={"schema","vector_id","repo","repo_sha","contract","authority_ceiling","on_violation","work_id","work_order_digest"}
def digest(o): return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def verify(p):
 o=json.loads(p.read_text()); miss=REQ-set(o)
 if miss:return False,"missing:"+",".join(sorted(miss))
 if o["schema"]!="sa2a/fleet-conformance/v1":return False,"schema"
 if len(o["repo_sha"])!=40 or any(c not in "0123456789abcdef" for c in o["repo_sha"]):return False,"repo_sha"
 if o["authority_ceiling"]!="none":return False,"authority_escalation"
 if o["on_violation"]!="reject":return False,"non_fail_closed"
 return True,digest(o)
def main():
 ap=argparse.ArgumentParser();ap.add_argument("root",nargs="?",default="conformance/sa2a/fleet-v26.9.29/vectors");ns=ap.parse_args()
 fs=sorted(Path(ns.root).glob("*.json"))
 if not fs:raise SystemExit("REFUSED:no_vectors")
 bad=[(p.name,d) for p in fs for ok,d in [verify(p)] if not ok]
 if bad:
  [print(f"REFUSED:{n}:{d}") for n,d in bad];raise SystemExit(1)
 print(f"ADMITTED:{len(fs)} vectors")
if __name__=="__main__":main()
