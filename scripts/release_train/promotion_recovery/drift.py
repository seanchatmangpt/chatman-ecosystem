from enum import Enum
class DriftKind(str,Enum):
    CURRENT='CURRENT'; CUT='CUT'; POLICY='POLICY'; FRONTIER='FRONTIER'; LEASE='LEASE'; MULTI='MULTI'

def classify(intent, policy, frontier, now):
    kinds=[]
    selected=frontier.select(policy.strategy).cut_id
    if selected!=intent.cut_id: kinds.append('CUT')
    if policy.digest!=intent.policy_digest: kinds.append('POLICY')
    if frontier.digest!=intent.frontier_digest: kinds.append('FRONTIER')
    if not intent.lease.active(now): kinds.append('LEASE')
    if not kinds: return DriftKind.CURRENT
    if len(kinds)>1: return DriftKind.MULTI
    return DriftKind(kinds[0])
