def project(event, census):
    return tuple({
        "activity":"invalidation_acknowledgement",
        "producer_repo":event.producer.repo,
        "producer_sha":event.producer.sha,
        "event_id":event.event_id,
        "consumer_repo":consumer.repo,
        "consumer_sha":consumer.sha,
        "cascade_depth":depth,
        "state":state,
        "time":event.observed_at.isoformat(),
    } for consumer,depth,state in census)
