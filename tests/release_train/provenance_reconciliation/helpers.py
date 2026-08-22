from scripts.release_train.provenance_reconciliation.claims import EvidenceClaim
from scripts.release_train.provenance_reconciliation.model import ExactSubject
from scripts.release_train.provenance_reconciliation.provenance import EvidenceRecord

SHA_A = "a" * 40
SHA_B = "b" * 40
DIGEST = "d" * 64
SUBJECT_A = ExactSubject("seanchatmangpt/chatman-ecosystem", SHA_A)
SUBJECT_B = ExactSubject("seanchatmangpt/gymact", SHA_B)


def records_for(subject, when="2026-08-22T09:00:00Z"):
    return [EvidenceRecord(f"{subject.repo}:{scope}", subject, "ci_run", when, "https://api.github.com/example", DIGEST, run_id=100 + i) for i, scope in enumerate(("focused", "integration", "e2e", "replay", "security", "repository"))]


def claims_for(subject, repository="ALIVE"):
    scopes = ("focused", "integration", "e2e", "replay", "security", "repository")
    return [EvidenceClaim(f"claim:{subject.repo}:{scope}", subject, scope, repository if scope == "repository" else "ALIVE", (f"{subject.repo}:{scope}",)) for scope in scopes]
