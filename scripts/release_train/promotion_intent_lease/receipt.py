from dataclasses import dataclass
import hashlib, json

@dataclass(frozen=True)
class Receipt:
    payload: dict
    digest: str

    @classmethod
    def manufacture(cls, payload: dict) -> 'Receipt':
        p=dict(payload); p['actuation_performed']=False
        raw=json.dumps(p,sort_keys=True,separators=(',',':')).encode()
        return cls(p, hashlib.sha256(raw).hexdigest())

    def replay(self) -> bool:
        raw=json.dumps(self.payload,sort_keys=True,separators=(',',':')).encode()
        return self.payload.get('actuation_performed') is False and hashlib.sha256(raw).hexdigest()==self.digest
