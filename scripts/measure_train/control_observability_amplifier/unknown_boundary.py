def observe(rows):
 u=[r for r in rows if r.get('standing')=='UNKNOWN']
 return {"sensor":"unknown_boundary","count":len(u),"subjects":sorted(r['subject'] for r in u)}
