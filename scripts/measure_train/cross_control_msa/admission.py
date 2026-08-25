from .refusal import Refused
def admit(subject,rows,now):
 seen=set(); out=[]
 for r in rows:
  if r.subject!=subject: raise Refused("REFUSED[FOREIGN_SUBJECT]")
  if r.observed_at>now: raise Refused("REFUSED[FUTURE_EVIDENCE]")
  key=(r.control.family,r.observation_id)
  if key in seen: raise Refused("REFUSED[DUPLICATE_EVIDENCE]")
  seen.add(key); out.append(r)
 return tuple(out)
