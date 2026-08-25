from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class RuntimeReceipt:
    topology: str
    transport: str
    encrypted: bool
    exit_status: int
    semantic_digest: str
    def admit(self):
        tls = "tls" in self.topology.lower()
        if tls and (self.transport != "inet_tls" or not self.encrypted):
            raise Refused("REFUSED[TLS_RECEIPT_TRANSPORT_CONTRADICTION]")
        if self.exit_status != 0: raise Refused("REFUSED[RUNTIME_EXIT_NONZERO]")
        if len(self.semantic_digest)!=64: raise Refused("REFUSED[INVALID_SEMANTIC_DIGEST]")
        return self
