from .admission import admit_event
from .cascade import build_cascade
from .standing import apply_standing
from .candidate import select_candidate
from .authority import require_authority
from .receipt import manufacture_receipt

def qualify_invalidation(bindings,event,current_standing,*,durable=False,transactional=False):
    admit_event(bindings,event)
    cascade=build_cascade(bindings,event)
    standings=apply_standing(current_standing,cascade)
    candidate=select_candidate(require_durable=durable,require_transactional=transactional)
    require_authority('CONSTRUCT')
    plan=[{'phase':'VERIFY','subject':i.subject,'reason':i.reason} for i in cascade]
    plan += [{'phase':'CONSTRUCT','subject':i.subject,'target_standing':standings[i.subject]} for i in cascade]
    payload={'producer':event.producer.key,'event':event.kind,'cascade':[i.__dict__ for i in cascade],
             'standings':standings,'candidate':candidate.name,'plan':plan,'standing':'PARTIAL_ALIVE'}
    return {'payload':payload,'receipt':manufacture_receipt(payload),'actuation_performed':False}
