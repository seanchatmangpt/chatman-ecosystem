from dataclasses import dataclass
from .subject import SubjectEpoch
from .refusal import Refused

@dataclass(frozen=True)
class RuntimeReceipt:
    subject: SubjectEpoch
    topology: str
    transport: str
    encrypted: bool
    cert_fingerprint: str
    exit_status: int

    def admit(self, expected: SubjectEpoch) -> "RuntimeReceipt":
        if self.subject != expected:
            raise Refused("RUNTIME_RECEIPT_FOREIGN_SUBJECT")
        if self.exit_status != 0:
            raise Refused("RUNTIME_EXECUTION_FAILED")
        tls_claim = "tls" in self.topology.lower()
        if tls_claim and (self.transport != "inet_tls" or not self.encrypted or not self.cert_fingerprint):
            raise Refused("TLS_RECEIPT_TRANSPORT_CONTRADICTION")
        return self
