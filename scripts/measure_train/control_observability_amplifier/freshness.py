from datetime import datetime, timezone
def observe(rows, max_age_s=3600):
 now=datetime.now(timezone.utc); stale=[r['id'] for r in rows if (now-r['observed_at']).total_seconds()>max_age_s]
 return {"sensor":"freshness","stale":stale,"standing":"ALIVE" if not stale else "UNKNOWN"}
