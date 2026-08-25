from .receipt import manufacture
from .subject import Refusal

def verify(receipt, subject, coherence, coverage, parent=None):
    expected=manufacture(subject,coherence,coverage,parent)
    if receipt != expected: raise Refusal("RECEIPT_MISMATCH")
    return True
