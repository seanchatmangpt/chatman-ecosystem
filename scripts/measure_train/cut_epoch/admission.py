from .subject import Refused
def admit_cut(cut, lease, current_cut, current_epochs, now):
    if now.tzinfo is None: raise Refused("REFUSED[NAIVE_NOW]")
    if lease.cut_id != cut.cut_id: raise Refused("REFUSED[LEASE_CUT_MISMATCH]")
    if now < lease.issued_at: raise Refused("REFUSED[CUT_LEASE_NOT_YET_VALID]")
    if now >= lease.expires_at: raise Refused("REFUSED[EXPIRED_CUT_LEASE]")
    if current_cut is None or cut.cut_id != current_cut.cut_id: raise Refused("REFUSED[SUPERSEDED_EVIDENCE_CUT]")
    current={e.subject.repo:e for e in current_epochs}
    selected=cut.by_repo()
    if set(selected)!=set(current): raise Refused("REFUSED[INCOMPLETE_CURRENT_CUT]")
    for repo,epoch in selected.items():
        if current[repo] != epoch: raise Refused("REFUSED[STALE_CUT_PRODUCER_EPOCH]")
    return "ADMITTED"
