def project(event, cascade_rows):
    return tuple({
        "activity":"invalidate_binding",
        "producer_repo":event.producer.repo,
        "producer_sha":event.producer.sha,
        "event_id":event.event_id,
        "kind":event.kind,
        "binding_id":binding_id,
        "cascade_depth":depth,
        "time":event.observed_at.isoformat(),
    } for binding_id,depth in sorted(cascade_rows))
