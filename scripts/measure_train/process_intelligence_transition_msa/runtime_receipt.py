from .subject import Refused

def admit_runtime_receipt(payload, expected_sha):
    if payload.get("source_sha") != expected_sha:
        raise Refused("REFUSED[FOREIGN_RUNTIME_RECEIPT]")

    if payload.get("exit_status") != 0:
        raise Refused("REFUSED[RUNTIME_EXECUTION_FAILED]")

    environment = payload.get("environment") or {}
    distribution = environment.get("distribution") or {}
    topology = str(payload.get("topology") or "")

    if "inet_tls" in topology:
        if distribution.get("transport") != "inet_tls":
            raise Refused("REFUSED[TLS_RECEIPT_TRANSPORT_CONTRADICTION]")
        if distribution.get("encrypted") is not True:
            raise Refused("REFUSED[TLS_RECEIPT_ENCRYPTION_CONTRADICTION]")
        if distribution.get("production_network_standing") == "blocked":
            raise Refused("REFUSED[TLS_RECEIPT_PRODUCTION_NETWORK_BLOCKED]")

    return {
        "source_sha": expected_sha,
        "runtime": "PASS",
        "network_security": (
            "PASS"
            if distribution.get("encrypted") is True
            else "UNSAFE_OR_UNPROVEN"
        ),
    }
