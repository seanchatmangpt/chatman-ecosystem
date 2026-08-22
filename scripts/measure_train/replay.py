from __future__ import annotations
from .identity import Refused, RefusalCode
from .receipts import Receipt, manufacture
from .evidence import Evidence

def verify(receipt: Receipt, rows: tuple[Evidence,...])->bool:
    expected=manufacture(receipt.subject,rows,receipt.parent_digests)
    if expected != receipt: raise Refused(RefusalCode.RECEIPT_MISMATCH,"receipt body or digest differs")
    return True
