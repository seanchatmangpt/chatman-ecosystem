from collections import deque

def cascade(bindings, event):
    consumers_by_producer={}
    bindings_by_consumer={}
    for b in bindings:
        consumers_by_producer.setdefault(b.producer, []).append(b.consumer)
        bindings_by_consumer.setdefault(b.consumer, []).append(b)
    q=deque([event.producer]); seen={event.producer}; affected={}
    depth=0
    while q:
        for _ in range(len(q)):
            producer=q.popleft()
            for consumer in sorted(consumers_by_producer.get(producer, ())):
                if consumer not in seen:
                    seen.add(consumer); q.append(consumer)
                for b in bindings_by_consumer.get(consumer, ()):
                    if b.producer==producer:
                        affected[b.binding_id]=depth+1
        depth+=1
    return tuple(sorted(affected.items()))
