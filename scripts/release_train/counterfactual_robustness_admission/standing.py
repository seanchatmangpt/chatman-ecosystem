def derive(*,blockers=(),failed=False,robust=False,supported=True):
    if blockers: return 'BLOCKED'
    if failed: return 'BUILD_BROKEN'
    if not supported: return 'UNKNOWN'
    if robust: return 'PARTIAL_ALIVE'
    return 'UNKNOWN'
