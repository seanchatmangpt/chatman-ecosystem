#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
SHA=re.compile(r"^[0-9a-f]{40}$")
def dt(v):return datetime.fromisoformat(v.replace("Z","+00:00")).astimezone(timezone.utc)
def evaluate(data):
    f=[]
    if data.get("schema")!="https://chatman.dev/fleet/recent-activity/v1":f.append("REFUSED[SCHEMA]")
    if data.get("owner")!="seanchatmangpt":f.append("REFUSED[OWNER]")
    if data.get("authority")!="NONE" or data.get("standing")!="OBSERVED":f.append("REFUSED[PROMOTION]")
    s=data.get("subject",{})
    if s.get("repository")!="seanchatmangpt/chatman-ecosystem" or not SHA.fullmatch(str(s.get("base_sha",""))):f.append("REFUSED[SUBJECT]")
    try:start,end=dt(data["window"]["start"]),dt(data["window"]["end"])
    except Exception:start=end=None;f.append("REFUSED[WINDOW]")
    repos=data.get("repositories",[])
    if data.get("repository_count")!=len(repos):f.append("REFUSED[COUNT]")
    names=[r.get("repository") for r in repos]
    if names!=sorted(names):f.append("REFUSED[ORDER]")
    if len(names)!=len(set(names)):f.append("REFUSED[DUPLICATE_REPOSITORY]")
    for r in repos:
        n=str(r.get("repository",""))
        if not n.startswith("seanchatmangpt/"):f.append(f"REFUSED[FOREIGN]:{n}")
        if not r.get("default_branch"):f.append(f"REFUSED[BRANCH]:{n}")
        if not SHA.fullmatch(str(r.get("observed_sha",""))):f.append(f"REFUSED[SHA]:{n}")
        if r.get("authority")!="NONE" or r.get("standing")!="OBSERVED":f.append(f"REFUSED[ROW_PROMOTION]:{n}")
        try:
            t=dt(r["commit_timestamp"])
            if start and end and not(start<=t<=end):f.append(f"REFUSED[OUTSIDE_WINDOW]:{n}")
        except Exception:f.append(f"REFUSED[TIMESTAMP]:{n}")
        if n=="seanchatmangpt/ggen" and r.get("read_only") is not True:f.append("REFUSED[GGEN_NOT_READ_ONLY]")
    body={"schema":"https://chatman.dev/fleet/recent-activity/receipt/v1","subject":s,"repository_count":len(repos),"authority":"NONE","findings":sorted(set(f))}
    body["standing"]="ALIVE" if not f else "REFUSED";body["digest"]="sha256:"+hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();return body,0 if not f else 2
def main():
    p=argparse.ArgumentParser();p.add_argument("snapshot");a=p.parse_args();r,c=evaluate(json.loads(Path(a.snapshot).read_text()));print(json.dumps(r,indent=2,sort_keys=True));return c
if __name__=="__main__":raise SystemExit(main())
