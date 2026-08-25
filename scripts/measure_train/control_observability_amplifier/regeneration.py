def observe(rows):
 bad=[r['subject'] for r in rows if r.get('first_digest')!=r.get('replay_digest')]
 return {"sensor":"regeneration","nondeterministic":sorted(bad),"standing":"ALIVE" if not bad else "BUILD_BROKEN[NONDETERMINISTIC_REGENERATION]"}
