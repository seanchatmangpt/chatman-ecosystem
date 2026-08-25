import hashlib, json

def manufacture_receipt(subject, census_rows, diversity, standing_value, policy, parent=None):
    eff=diversity["effective_sources"]
    body={
        "schema":"chatman.measure-witness-independence/1",
        "repo":subject.repo,
        "sha":subject.sha,
        "census":[{
            "cluster_id":r["cluster_id"],
            "members":list(r["members"]),
            "scopes":list(r["scopes"]),
            "state":r["state"],
        } for r in census_rows],
        "diversity":{
            "producers":diversity["producers"],
            "source_kinds":diversity["source_kinds"],
            "effective_sources":f"{eff.numerator}/{eff.denominator}",
        },
        "policy":{
            "min_independent_clusters":policy.min_independent_clusters,
            "required_scope":policy.required_scope,
        },
        "standing":standing_value,
        "parent":parent,
        "actuation_performed":False,
    }
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
