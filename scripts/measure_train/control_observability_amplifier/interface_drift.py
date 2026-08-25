def observe(rows):
 bad=[r['subject'] for r in rows if r.get('expected_interface')!=r.get('observed_interface')]
 return {"sensor":"interface_drift","incompatible":sorted(bad),"count":len(bad)}
