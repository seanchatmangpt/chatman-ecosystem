from dataclasses import replace
from .subject import Refusal

def renew_binding(binding, *, producer=None, receipt=None, schema=None):
    producer = producer or binding.producer
    receipt = receipt or binding.receipt
    schema = schema or binding.schema
    if producer.repo != binding.producer.repo:
        raise Refusal('REFUSED[FOREIGN_PRODUCER_RENEWAL]')
    if schema != binding.schema:
        raise Refusal('REFUSED[SCHEMA_DRIFT_REQUIRES_REQUALIFICATION]')
    if producer == binding.producer and receipt == binding.receipt:
        raise Refusal('REFUSED[NO_RENEWAL_DELTA]')
    return replace(binding, producer=producer, receipt=receipt)
