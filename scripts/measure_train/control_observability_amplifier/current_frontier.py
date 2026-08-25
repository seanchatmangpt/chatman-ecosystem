def observe(rows):
 cur=[r for r in rows if r.get('current')]; digests={r['semantic_digest'] for r in cur}
 return {"sensor":"current_frontier","count":len(cur),"standing":"ALIVE" if len(digests)==1 and cur else "REFUSED[SPLIT_OR_EMPTY_CURRENT_FRONTIER]"}
