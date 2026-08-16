#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json, re
from pathlib import Path

RECEIPT_SCHEMA="chatman.qlever-crown.receipt/v1"
ENGINE_COMMIT="bd25c13adbb42963017d9964579a485de191b12f"
CONTROL_COMMIT="72226eb91dd4e0ca5af30e4b8786a788a374d6fe"

def sha256_bytes(b: bytes)->str: return hashlib.sha256(b).hexdigest()
def canonical(obj)->bytes: return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def parse_tsv(path: Path):
    rows=list(csv.reader(path.read_text().splitlines(),delimiter="\t"))
    if not rows: raise ValueError("REFUSED:EMPTY_QUERY_RESULT")
    return rows[0],rows[1:]

def iri_id(value:str)->int:
    m=re.fullmatch(r"<urn:chatman:subject:(\d+)>",value)
    if not m: raise ValueError("REFUSED:UNEXPECTED_CANDIDATE_IRI")
    return int(m.group(1))

def expected_candidates(subjects:int, predicates:int, limit:int=25):
    vals=[f"<urn:chatman:subject:{i}>" for i in range(1,subjects) if i % predicates == 0]
    # SPARQL ORDER BY STR(?candidate) sorts the lexical IRI, not its TSV
    # serialization.  Strip the RDF-term angle brackets before comparison.
    return sorted(vals,key=lambda value:value[1:-1])[:limit]

def verify(fixture_path:Path, ranking_path:Path, replay_path:Path, count_path:Path, subject_sha:str):
    fixture=json.loads(fixture_path.read_text())
    if fixture.get("schema")!="chatman.qlever.fixture/v1": raise ValueError("REFUSED:FIXTURE_SCHEMA")
    if fixture["triples"] != fixture["subjects"]*fixture["width"]: raise ValueError("REFUSED:FIXTURE_CARDINALITY")
    if fixture["triples"] < 2_000_000: raise ValueError("REFUSED:QLEVER_SCALE_BELOW_2M")
    h1,r1=parse_tsv(ranking_path); h2,r2=parse_tsv(replay_path)
    if h1!=["?candidate","?overlap"]: raise ValueError(f"REFUSED:RANKING_HEADER:{h1}")
    if (h1,r1)!=(h2,r2): raise ValueError("REFUSED:QUERY_REPLAY_DRIFT")
    expected=expected_candidates(fixture["subjects"],fixture["predicate_universe"],25)
    got=[row[0] for row in r1]
    if got!=expected: raise ValueError("REFUSED:STRUCTURAL_RANKING_MISMATCH")
    if any(len(row)!=2 or int(row[1])!=fixture["width"] for row in r1): raise ValueError("REFUSED:STRUCTURAL_OVERLAP_MISMATCH")
    jaccards=[int(row[1])/(2*fixture["width"]-int(row[1])) for row in r1]
    if any(x!=1.0 for x in jaccards): raise ValueError("REFUSED:JACCARD_DERIVATION")
    hc,rc=parse_tsv(count_path)
    if hc!=["?triples"] or len(rc)!=1 or int(rc[0][0])!=fixture["triples"]: raise ValueError("REFUSED:QLEVER_TRIPLE_COUNT")
    payload={
      "schema":RECEIPT_SCHEMA,"subject_sha":subject_sha,"qlever_engine_commit":ENGINE_COMMIT,"qlever_control_commit":CONTROL_COMMIT,
      "fixture":fixture,"query_result_sha256":sha256_bytes(ranking_path.read_bytes()),"query_replay_sha256":sha256_bytes(replay_path.read_bytes()),
      "triple_count_result_sha256":sha256_bytes(count_path.read_bytes()),"structural_similarity":"predicate-neighborhood-overlap+jaccard",
      "top_k":25,"observed_rows":len(r1),"execution_observed":True,"independent_verification":True,"replay_verified":True,
      "authority":"SELECT_ONLY","do_authority":False,"standing":"ALIVE"
    }
    receipt_id=sha256_bytes(canonical(payload)); payload["receipt_sha256"]=receipt_id
    return payload

def main():
    ap=argparse.ArgumentParser()
    for n in ["fixture","ranking","replay","count","subject-sha","receipt"]: ap.add_argument("--"+n,required=True)
    a=ap.parse_args(); p=verify(Path(a.fixture),Path(a.ranking),Path(a.replay),Path(a.count),a.subject_sha); Path(a.receipt).write_text(json.dumps(p,sort_keys=True,indent=2)+"\n"); print(f"QLEVER_CROWN=ALIVE triples={p['fixture']['triples']} receipt_sha256={p['receipt_sha256']} do_authority=false")
if __name__=="__main__": main()
