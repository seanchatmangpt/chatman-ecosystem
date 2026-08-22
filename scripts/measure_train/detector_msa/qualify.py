from .consensus import consensus
from .standing import bounded_standing
from .receipt import manufacture_receipt

def qualify(subject, frontier, votes, independent_pairs=frozenset(), rail_outcomes=(), parent_receipt=None):
    result = consensus(votes, independent_pairs)
    standing = bounded_standing(result, rail_outcomes)
    receipt = manufacture_receipt(subject, frontier, result, standing, parent_receipt)
    telemetry = tuple(
        {
            "activity": "measure_detector_msa",
            "repo": subject.repo,
            "sha": subject.sha,
            "detector_id": vote.detector_id,
            "source_fingerprint": vote.source_fingerprint,
            "state": vote.state,
            "evidence_id": vote.evidence_id,
        }
        for vote in sorted(votes)
    )
    return {
        "consensus": result,
        "standing": standing,
        "receipt": receipt,
        "telemetry": telemetry,
        "actuation_performed": False,
    }
