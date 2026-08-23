from .receipt import Receipt

def replay(receipt: Receipt, expected_digest: str) -> bool:
    return (not receipt.actuation_performed) and receipt.digest() == expected_digest
