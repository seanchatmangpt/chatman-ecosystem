from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from .receipt import canonical_bytes, replay
from .train import manufacture_train

def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(prog="release-train")
    sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("manufacture"); p.add_argument("--input",required=True); p.add_argument("--output",required=True)
    r=sub.add_parser("replay"); r.add_argument("--receipt",required=True)
    args=parser.parse_args(argv)
    if args.command=="manufacture":
        spec=json.loads(Path(args.input).read_text())
        doc=manufacture_train(spec)
        Path(args.output).write_bytes(canonical_bytes(doc)+b"\n")
        return 0
    doc=json.loads(Path(args.receipt).read_text())
    replay(doc)
    sys.stdout.write("REPLAY_MATCH\n")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
