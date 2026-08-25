from .refusal import refuse
def require_correspondence(*digests):
    if not digests or "" in digests or len(set(digests))!=1:
        refuse("REACTOR_CORRESPONDENCE_DIVERGENCE")
    return True
