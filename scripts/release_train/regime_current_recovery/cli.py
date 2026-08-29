import json, sys
from datetime import datetime
from .receipt import canonical

def normalize(payload: dict) -> bytes:
    required={'subject','standing','reason','decision','statistic','regimes','blockers','store','alternatives','phases'}
    missing=sorted(required-payload.keys())
    if missing: raise ValueError(f'REFUSED[MISSING_CLI_FIELDS:{",".join(missing)}]')
    payload=dict(payload); payload['observed_at']=datetime.fromisoformat(payload['observed_at']).isoformat() if 'observed_at' in payload else None
    return canonical(payload)+b'\n'

def main() -> int:
    sys.stdout.buffer.write(normalize(json.load(sys.stdin))); return 0

if __name__=='__main__': raise SystemExit(main())
