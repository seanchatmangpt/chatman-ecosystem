from collections import defaultdict
from .confusion import confusion
from .loss import realized_loss

def stratify(policy,rows,field):
    valid={"strategy","methodology","engine","region","evidence_root"}
    if field not in valid: raise ValueError("unsupported stratum")
    groups=defaultdict(list)
    for row in rows: groups[getattr(row,field)].append(row)
    return {key:{"confusion":confusion(group),"loss":realized_loss(policy,group)} for key,group in sorted(groups.items())}
