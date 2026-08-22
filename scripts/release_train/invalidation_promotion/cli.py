import json, sys
from datetime import datetime
from .subject import Subject
from .binding import PromotionBinding
from .event import InvalidationEvent
from .engine import qualify_invalidation

def main():
    data=json.load(sys.stdin)
    bindings=[PromotionBinding(Subject(*b['consumer']),Subject(*b['producer']),b['receipt'],b['schema'],b['scope'],b['binding_id']) for b in data['bindings']]
    e=data['event']; event=InvalidationEvent(Subject(*e['producer']),e['kind'],datetime.fromisoformat(e['observed_at']),e.get('replacement_receipt'))
    out=qualify_invalidation(bindings,event,data.get('standing',{}),durable=data.get('durable',False),transactional=data.get('transactional',False))
    json.dump(out,sys.stdout,sort_keys=True,separators=(',',':')); sys.stdout.write('\n')
if __name__=='__main__': main()
