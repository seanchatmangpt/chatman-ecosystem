from .subject import Refused

def check_transition(t):
    if t.expected_revision != t.before.revision or t.expected_digest != t.before.digest: return "STALE_TOKEN"
    if t.outcome == "COMMITTED":
        if t.after is None: raise Refused("REFUSED[COMMIT_WITHOUT_AFTER]")
        if t.after.subject != t.before.subject: raise Refused("REFUSED[FOREIGN_AFTER_SUBJECT]")
        if t.after.revision != t.before.revision + 1: return "REVISION_VIOLATION"
        if t.after.generation < t.before.generation: return "GENERATION_REGRESSION"
        if t.after.digest == t.before.digest: return "DIGEST_NOT_ADVANCED"
    return "PASS"
