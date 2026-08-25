import unittest
from scripts.measure_train.process_intelligence_transition_msa.runtime_receipt import admit_runtime_receipt
from scripts.measure_train.process_intelligence_transition_msa.subject import Refused

class T(unittest.TestCase):
    def test_tls_label_cannot_launder_plain_distribution(self):
        payload = {
            "source_sha": "a"*40,
            "exit_status": 0,
            "topology": "three same-host OTP peer nodes plus origin over inet_tls",
            "environment": {
                "distribution": {
                    "transport": "inet_tcp",
                    "encrypted": False,
                    "production_network_standing": "blocked",
                }
            },
        }
        with self.assertRaisesRegex(Refused, "TLS_RECEIPT_TRANSPORT_CONTRADICTION"):
            admit_runtime_receipt(payload, "a"*40)
