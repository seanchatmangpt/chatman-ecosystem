def project(subject,transitions,conflicts):
    conflict_by_event={event_id:kind for event_id,kind in conflicts}
    return tuple({"activity":"measure_policy_state_transition","repo":subject.repo,"sha":subject.sha,"event_id":t.event_id,"writer":t.writer_id,"outcome":t.outcome,"before_revision":t.before.revision,"after_revision":None if t.after is None else t.after.revision,"conflict":conflict_by_event.get(t.event_id),"time":t.completed_at.isoformat()} for t in sorted(transitions,key=lambda x:(x.completed_at,x.event_id)))
