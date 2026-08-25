REQUIRED={'discovery','conformance','simulation','prediction','optimization','intervention','monitoring','event-centric','object-centric','declarative','procedural'}
def observe(methods):
 missing=sorted(REQUIRED-set(methods)); return {'sensor':'methodology_coverage','missing':missing,'coverage':(len(REQUIRED)-len(missing))/len(REQUIRED)}
