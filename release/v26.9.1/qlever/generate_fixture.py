#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

SCHEMA = "chatman.qlever.fixture/v1"

def generate(output: Path, subjects: int, width: int, predicates: int = 32) -> dict:
    if subjects < 2 or width < 1 or predicates < width:
        raise ValueError("REFUSED:INVALID_FIXTURE_BOUNDS")
    h = hashlib.sha256()
    triples = 0
    with output.open("wb") as f:
        for i in range(subjects):
            for j in range(width):
                p = (i + j) % predicates
                line = f"<urn:chatman:subject:{i}> <urn:chatman:predicate:{p}> <urn:chatman:value:{j}> .\n".encode()
                f.write(line); h.update(line); triples += 1
    return {"schema":SCHEMA,"subjects":subjects,"width":width,"predicate_universe":predicates,"triples":triples,"sha256":h.hexdigest()}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); ap.add_argument("--manifest",required=True); ap.add_argument("--subjects",type=int,default=200_000); ap.add_argument("--width",type=int,default=10); ap.add_argument("--predicates",type=int,default=32)
    a=ap.parse_args(); out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); m=generate(out,a.subjects,a.width,a.predicates); Path(a.manifest).write_text(json.dumps(m,sort_keys=True,separators=(",",":"))+"\n"); print(f"QLEVER_FIXTURE triples={m['triples']} sha256={m['sha256']}")
if __name__=="__main__": main()
