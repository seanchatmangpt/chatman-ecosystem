#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
API="https://api.github.com"
def request(path,token):
    h={"Accept":"application/vnd.github+json","User-Agent":"chatman-fleet-recent-observer/1","X-GitHub-Api-Version":"2022-11-28"}
    if token:h["Authorization"]=f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(API+path,headers=h),timeout=30) as r:return json.loads(r.read().decode())
def observe(owner,since,token):
    q=urllib.parse.quote(f"user:{owner} pushed:>={since}");repos=[];page=1
    while True:
        p=request(f"/search/repositories?q={q}&sort=updated&order=desc&per_page=100&page={page}",token);items=p.get("items",[])
        if not items:break
        repos.extend(items)
        if len(items)<100:break
        page+=1
    rows=[]
    for repo in repos:
        full,branch=repo["full_name"],repo["default_branch"];c=request(f"/repos/{full}/commits/{urllib.parse.quote(branch,safe='')}",token)
        rows.append({"repository":full,"default_branch":branch,"observed_sha":c["sha"],"commit_timestamp":c["commit"]["committer"]["date"],"latest_message":c["commit"]["message"].splitlines()[0],"authority":"NONE","standing":"OBSERVED","read_only":full=="seanchatmangpt/ggen"})
    return sorted(rows,key=lambda x:x["repository"])
def main():
    p=argparse.ArgumentParser();p.add_argument("--owner",default="seanchatmangpt");p.add_argument("--since",required=True);p.add_argument("--subject-sha",required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    rows=observe(a.owner,a.since,os.environ.get("GITHUB_TOKEN"));now=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
    data={"schema":"https://chatman.dev/fleet/recent-activity/v1","observation_id":f"fleet:recent:{now[:10]}","owner":a.owner,"window":{"start":a.since+"T00:00:00Z","end":now},"query":f"user:{a.owner} pushed:>={a.since}","subject":{"repository":"seanchatmangpt/chatman-ecosystem","base_sha":a.subject_sha},"repository_count":len(rows),"authority":"NONE","standing":"OBSERVED","semantics":["Observation evidence only; no release promotion."],"repositories":rows}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(data,indent=2)+"\n");return 0
if __name__=="__main__":raise SystemExit(main())
