from __future__ import annotations
import json, sys
from datetime import datetime
from .candidate import PromotionCandidate
from .dependency import DependencyGraph
from .evidence import Axis, Evidence, Outcome
from .engine import manufacture_promotion
from .requirements import ReleaseProfile
from .subject import Subject

def _subject(value: dict) -> Subject:
    return Subject(value["repo"], value["sha"])

def main() -> int:
    payload=json.load(sys.stdin)
    subjects={item["id"]:_subject(item) for item in payload["subjects"]}
    graph=DependencyGraph({subjects[k]:frozenset(subjects[d] for d in deps) for k,deps in payload.get("dependencies",{}).items()})
    rows={subject:[] for subject in subjects.values()}
    for row in payload.get("evidence",[]):
        subject=subjects[row["subject"]]
        rows.setdefault(subject,[]).append(Evidence(subject,Axis(row["axis"]),Outcome(row["outcome"]),datetime.fromisoformat(row["observed_at"]),row["source"]))
    candidates=[PromotionCandidate(c["id"],subjects[c["root"]],c["benefit"],c["reversibility"],c["dependency_relief"],c["risk"]) for c in payload["candidates"]]
    profile=ReleaseProfile(payload["profile"]["name"],frozenset(Axis(a) for a in payload["profile"]["required_axes"]))
    result=manufacture_promotion(candidates,graph,rows,profile,payload["predecessor_sha"])
    json.dump({"standing":result.standing,"selected_candidate":result.selected_candidate,"receipt":result.receipt},sys.stdout,sort_keys=True,separators=(",",":")); sys.stdout.write("\n")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
