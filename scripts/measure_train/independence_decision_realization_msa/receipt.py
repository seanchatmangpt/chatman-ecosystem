import hashlib,json

def manufacture(subject,policy,census_result,standing_value,voi=None,regret=None):
    def q(x):
        return [x.numerator,x.denominator] if hasattr(x,"numerator") and hasattr(x,"denominator") else x
    body={"schema":"chatman.measure-independence-decision-realization/1","repo":subject.repo,"sha":subject.sha,"semantic_digest":subject.semantic_digest,"policy_id":policy.policy_id,"policy_generation":policy.generation,"policy_digest":policy.digest,"census":{k:q(v) for k,v in sorted(census_result.items())},"voi":{k:q(v) for k,v in sorted((voi or {}).items())},"regret":{k:q(v) for k,v in sorted((regret or {}).items())},"standing":standing_value,"authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
