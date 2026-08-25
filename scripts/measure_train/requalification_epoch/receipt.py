import hashlib,json

def manufacture_receipt(epoch,census_rows,standing_value,parent=None):
    body={"schema":"chatman.measure-requalification-epoch/1","producer_repo":epoch.producer.repo,"producer_sha":epoch.producer.sha,"generation":epoch.generation,"event_id":epoch.event_id,"epoch_receipt":epoch.receipt_sha256,"census":[list(r) for r in census_rows],"standing":standing_value,"parent":parent,"actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
