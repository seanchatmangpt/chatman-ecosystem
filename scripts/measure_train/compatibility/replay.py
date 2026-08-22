from .receipt import make_receipt
def replay(receipt):
    b=receipt["body"]
    class S: pass
    s=S(); s.repo=b["repo"]; s.sha=b["sha"]
    expected=make_receipt(s,b["standing"],b["axes"],b.get("parent"))
    if expected["digest"] != receipt["digest"]:
        return "REFUSED[RECEIPT_MISMATCH]"
    return "REPLAY_MATCH"
