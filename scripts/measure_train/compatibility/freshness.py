from datetime import datetime, timezone
def parse(ts):
    dt=datetime.fromisoformat(ts.replace("Z","+00:00"))
    if dt.tzinfo is None: raise ValueError("REFUSED[NAIVE_TIME]")
    return dt.astimezone(timezone.utc)
def stale(row, now, ttl_seconds):
    age=(parse(now)-parse(row.observed_at)).total_seconds()
    if age < 0: raise ValueError("REFUSED[FUTURE_EVIDENCE]")
    return age > ttl_seconds
