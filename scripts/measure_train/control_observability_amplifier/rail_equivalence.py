def observe(rails):
 states={r['state'] for r in rails}; mixed=len(states)>1
 return {'sensor':'rail_equivalence','states':sorted(states),'mixed':mixed,'standing':'UNKNOWN' if mixed else (next(iter(states)) if states else 'UNKNOWN')}
