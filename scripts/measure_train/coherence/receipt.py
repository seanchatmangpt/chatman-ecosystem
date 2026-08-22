import hashlib, json
from .subject import Subject
from .coherence import Coherence

def manufacture(subject: Subject, coherence: Coherence, coverage, parent: str|None=None):
    body={"schema":"chatman.measure-coherence/1","subject":subject.key,"standing":coherence.standing.value,
          "satisfied":list(coherence.satisfied),"unsatisfied":list(coherence.unsatisfied),
          "coverage":[{"id":c.obligation.obligation_id,"state":c.state.value,"witness_count":c.witness_count} for c in coverage],
          "parent":parent,"actuation_performed":False}
    canonical=json.dumps(body,sort_keys=True,separators=(",",":"))
    digest=hashlib.sha256(canonical.encode()).hexdigest()
    return {"body":body,"digest":digest}
