import json
from .authority import ActionClass, require
from .drift import classify
from .recovery import recover
from .receipt import manufacture, replay

def qualify(*, intent, proof, policy, frontier, now, witness, recovery_strategy, dependency_graph, dependency_standings):
    require(ActionClass.SELECT)
    blocker=dependency_graph.blocker(dependency_standings)
    if blocker:
        standing='BLOCKED'; reason=f'DEPENDENCY_BLOCKED:{blocker}'; selected=None
    else:
        drift=classify(intent,policy,frontier,now)
        if drift.value=='CURRENT': proof.admit(policy,frontier)
        decision=recover(drift,witness,recovery_strategy)
        standing=decision.standing; reason=decision.reason; selected=frontier.select(policy.strategy).cut_id
    require(ActionClass.CONSTRUCT)
    plan=['VERIFY','CONSTRUCT']
    rec=manufacture({'intent_id':intent.intent_id,'selected_cut':selected,'recovery':recovery_strategy.value,'standing':standing,'reason':reason,'dependency_order':list(dependency_graph.order),'plan':plan})
    assert replay(rec)
    return {'standing':standing,'selected_cut':selected,'recovery':recovery_strategy.value,'reason':reason,'plan':plan,'receipt':rec,'actuation_performed':False}

def deterministic_json(**kwargs):
    return json.dumps(qualify(**kwargs),sort_keys=True,separators=(',',':'))+'\n'
