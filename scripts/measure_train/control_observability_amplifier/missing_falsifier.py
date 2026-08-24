def observe(capabilities, falsifiers):
 covered={f['capability'] for f in falsifiers}; missing=sorted(set(capabilities)-covered)
 return {"sensor":"missing_falsifier","missing":missing,"count":len(missing)}
