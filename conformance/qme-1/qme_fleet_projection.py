#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

OBS_SCHEMA="https://chatman.dev/fleet/recent-activity/v1"
PROJECTION_SCHEMA="chatman.qme-fleet-projection/1"
ROOT="seanchatmangpt/chatman-ecosystem"
GGEN="seanchatmangpt/ggen"
EQUATION="A = mu(O*)"

class Refusal(Exception):
    def __init__(self, code, detail):
        super().__init__(detail); self.code=code; self.detail=detail

def refuse(code, detail): raise Refusal(code, detail)
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def check(observation, projection):
    if observation.get("schema")!=OBS_SCHEMA: refuse("SOURCE_SCHEMA_INVALID","fleet observation schema")
    if observation.get("authority")!="NONE": refuse("SOURCE_AUTHORITY_PROMOTION",str(observation.get("authority")))
    if observation.get("standing")!="OBSERVED": refuse("SOURCE_STANDING_PROMOTION",str(observation.get("standing")))
    rows=observation.get("repositories")
    if not isinstance(rows,list) or observation.get("repository_count")!=len(rows): refuse("SOURCE_COUNT_DRIFT","repository_count mismatch")
    by_repo={}
    for row in rows:
        name=row.get("repository")
        if name in by_repo: refuse("SOURCE_DUPLICATE_REPOSITORY",str(name))
        by_repo[name]=row
        if row.get("authority")!="NONE" or row.get("standing")!="OBSERVED": refuse("SOURCE_ROW_PROMOTION",str(name))
    if GGEN not in by_repo or by_repo[GGEN].get("read_only") is not True: refuse("GGEN_WRITE_PROMOTION","ggen must remain read-only")
    if projection.get("schema")!=PROJECTION_SCHEMA: refuse("PROJECTION_SCHEMA_INVALID","unexpected projection schema")
    if projection.get("authority")!="NONE" or projection.get("consequence")!="EVIDENCE_ONLY": refuse("PROJECTION_AUTHORITY_PROMOTION","projection is evidence-only")
    if projection.get("standing")!="PARTIAL_ALIVE": refuse("PROJECTION_STANDING_PROMOTION",str(projection.get("standing")))
    if projection.get("canonical_equation")!=EQUATION: refuse("EQUATION_DRIFT",str(projection.get("canonical_equation")))
    source=projection.get("source") or {}; subject=observation.get("subject") or {}
    if source.get("observation_id")!=observation.get("observation_id"): refuse("SOURCE_ID_DRIFT",str(source.get("observation_id")))
    if source.get("repository_count")!=observation.get("repository_count"): refuse("SOURCE_COUNT_DRIFT","projection source count")
    if source.get("subject_repository")!=ROOT or source.get("subject_repository")!=subject.get("repository") or source.get("subject_base_sha")!=subject.get("base_sha"): refuse("SOURCE_SUBJECT_DRIFT","projection must bind exact fleet subject")
    sets=projection.get("capability_sets")
    if not isinstance(sets,list) or not sets: refuse("CAPABILITY_SETS_MISSING","empty capability sets")
    ids=[x.get("id") for x in sets]
    if len(ids)!=len(set(ids)): refuse("DUPLICATE_CAPABILITY_SET","ids must be unique")
    observed=set(by_repo)
    for item in sets:
        if item.get("authority_effect")!="NONE": refuse("PROJECTION_AUTHORITY_PROMOTION",str(item.get("id")))
        members=item.get("members")
        if not isinstance(members,list) or not members or len(members)!=len(set(members)): refuse("CAPABILITY_SET_INVALID",str(item.get("id")))
        missing=sorted(set(members)-observed)
        if missing: refuse("UNOBSERVED_CAPABILITY",f"{item.get('id')}:{','.join(missing)}")
    return {"schema":"chatman.qme-fleet-projection.receipt/1","source_observation_id":observation["observation_id"],"source_digest":"sha256:"+digest(observation),"projection_digest":"sha256:"+digest(projection),"repository_count":len(rows),"capability_set_count":len(sets),"authority":"NONE","consequence":"EVIDENCE_ONLY","standing":"PARTIAL_ALIVE","canonical_equation":EQUATION}

def main(argv=None):
    argv=argv or sys.argv
    if len(argv)!=3: print("usage: qme_fleet_projection.py OBSERVATION.json PROJECTION.json",file=sys.stderr); return 2
    try:
        print(json.dumps(check(json.loads(Path(argv[1]).read_text()),json.loads(Path(argv[2]).read_text())),sort_keys=True,separators=(",",":"))); return 0
    except Refusal as exc:
        print(f"REFUSED:{exc.code}:{exc.detail}",file=sys.stderr); return 1

if __name__=="__main__": raise SystemExit(main())
