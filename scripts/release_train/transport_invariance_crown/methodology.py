from .refusal import require

REQUIRED_METHODS=frozenset({
    'discovery','conformance','simulation','prediction','optimization','intervention','monitoring',
    'event_centric','object_centric','declarative','procedural'
})

def admit_methodologies(methods: set[str] | frozenset[str]) -> tuple[str,...]:
    missing=REQUIRED_METHODS-set(methods)
    require(not missing,"INCOMPLETE_METHODOLOGY_CLOSURE",','.join(sorted(missing)))
    return tuple(sorted(REQUIRED_METHODS))
