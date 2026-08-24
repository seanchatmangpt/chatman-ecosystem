import hashlib,json
def manufacture(subject,cal,capital,standing):
    body={'schema':'chatman.measure-federation-convergence-realization/1','repo':subject.repo,'sha':subject.sha,'semantic_digest':subject.semantic_digest,'generation':subject.generation,'support':cal.support,'false_fixed':[cal.false_fixed.numerator,cal.false_fixed.denominator],'capital':[capital.numerator,capital.denominator],'standing':standing,'authority':'OBSERVE|VERIFY','actuation_performed':False}
    raw=json.dumps(body,sort_keys=True,separators=(',',':')); return {'body':body,'sha256':hashlib.sha256(raw.encode()).hexdigest()}
