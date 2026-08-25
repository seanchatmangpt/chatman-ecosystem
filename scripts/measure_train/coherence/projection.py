def to_ocel(subject, witnesses, coverage):
    events=[]
    for i,w in enumerate(sorted(witnesses,key=lambda x:(x.observed_at.isoformat(),x.axis.value,x.scope,x.source))):
        events.append({"event_id":f"witness:{i}","activity":"MEASURE_WITNESS","time":w.observed_at.isoformat(),
                       "subject":subject.key,"axis":w.axis.value,"scope":w.scope,"outcome":w.outcome.value,"source":w.source})
    for c in coverage:
        events.append({"event_id":f"obligation:{c.obligation.obligation_id}","activity":"MEASURE_COVERAGE",
                       "subject":subject.key,"obligation":c.obligation.obligation_id,"state":c.state.value})
    return tuple(events)
