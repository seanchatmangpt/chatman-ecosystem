from .refusal import refuse
REQUIRED=frozenset("DISCOVERY CONFORMANCE SIMULATION PREDICTION OPTIMIZATION INTERVENTION MONITORING EVENT_CENTRIC OBJECT_CENTRIC DECLARATIVE PROCEDURAL".split())
def require_methodologies(values):
    missing=REQUIRED-set(values)
    if missing: refuse("MISSING_METHODOLOGIES",",".join(sorted(missing)))
    return True
