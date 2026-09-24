"""Chatman Ecosystem cross-product court.

This package evaluates correspondence among already-produced formal evidence.
It owns no solver, runtime actuation, authority grant, or external consequence.
"""

from .evaluator import evaluate
from .model import (
    CrossProductCase,
    CrossProductReceipt,
    EvidenceRecord,
    EvidenceResult,
    Formalism,
    MutantExpectation,
    RelationRequirement,
    Standing,
    SubjectBinding,
)

__all__ = [
    "CrossProductCase",
    "CrossProductReceipt",
    "EvidenceRecord",
    "EvidenceResult",
    "Formalism",
    "MutantExpectation",
    "RelationRequirement",
    "Standing",
    "SubjectBinding",
    "evaluate",
]
