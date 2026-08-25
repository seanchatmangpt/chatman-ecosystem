def producer_frontier(evidence):
    by_subject = {}
    for item in sorted(evidence, key=lambda x: (x.subject.repo, x.subject.sha, x.receipt_sha256)):
        key = item.subject
        previous = by_subject.get(key)
        if previous is not None and previous.receipt_sha256 != item.receipt_sha256:
            return {"state":"DIVERGED","current":None}
        by_subject[key] = item
    if not by_subject:
        return {"state":"UNKNOWN","current":None}
    if len(by_subject) != 1:
        return {"state":"DIVERGED","current":None}
    return {"state":"CURRENT","current":next(iter(by_subject.values()))}
