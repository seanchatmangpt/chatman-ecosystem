from .subject import Refused

def renew(binding, current_producer, current_receipt, current_schema):
    if binding.producer != current_producer:
        raise Refused("REFUSED[FOREIGN_RENEWAL_SUBJECT]")
    if len(current_receipt)!=64:
        raise Refused("REFUSED[INVALID_RENEWAL_RECEIPT]")
    if current_schema != binding.schema:
        raise Refused("REFUSED[RENEWAL_SCHEMA_DRIFT]")
    return type(binding)(binding.consumer, current_producer, current_receipt, current_schema, binding.scope, binding.binding_id)
