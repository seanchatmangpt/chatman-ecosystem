RED={'BUILD_BROKEN','BLOCKED'}
def observe(rows):
 red=sorted(r['subject'] for r in rows if r.get('standing') in RED)
 return {"sensor":"red_dependency","red":red,"standing":"BUILD_BROKEN" if red else "ALIVE"}
