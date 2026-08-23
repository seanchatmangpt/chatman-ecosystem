import hashlib,json
def manufacture_receipt(subject,plan,frontier,census,standing_value,parent=None):
    body={"schema":"chatman.measure-fusion-realization/1","repo":subject.repo,"sha":subject.sha,"plan_id":plan.plan_id,
          "frontier_digest":frontier.digest,"frontier_generation":frontier.generation,"census":list(census),"standing":standing_value,
          "parent":parent,"authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"),default=list)
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
