def observe(rows):
 drift=[r['subject'] for r in rows if r.get('declared_generator_digest')!=r.get('actual_generator_digest')]
 return {"sensor":"generator_drift","drift":sorted(drift),"count":len(drift)}
