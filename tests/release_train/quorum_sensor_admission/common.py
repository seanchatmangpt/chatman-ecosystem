from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fractions import Fraction
from scripts.release_train.quorum_sensor_admission import CalibrationFrontier, DependencyGraph, ReplicaVote, SensorCalibration, Subject, VectorClock, VisibilityObservation

SHA="a"*40; DEP_SHA="b"*40
SUBJECT=Subject.parse(f"seanchatmangpt/chatman-ecosystem@{SHA}")
DEP=Subject.parse(f"seanchatmangpt/gymact@{DEP_SHA}")
NOW=datetime(2026,8,23,1,30,tzinfo=timezone.utc)

def model(**overrides):
    data=dict(subject=SUBJECT,generation=7,support=100,false_current_rate=Fraction(1,100),false_stale_rate=Fraction(1,50),ambiguity_rate=Fraction(1,50),wilson_lower=Fraction(9,10),detector_family="replica-quorum-msa"); data.update(overrides); return SensorCalibration(**data)

def frontier(m=None):
    m=m or model(); return CalibrationFrontier.from_models(SUBJECT,[m])

def visibility(observed=("r1","r2","r3"),known=("r1","r2","r3"),lag=5):
    return VisibilityObservation(SUBJECT,tuple(observed),tuple(known),NOW-timedelta(seconds=10),lag)

def votes(generation=7,digest="c"*64): return [ReplicaVote(SUBJECT,r,generation,digest) for r in ("r1","r2","r3")]

def clocks(concurrent=False):
    if concurrent: return {"r1":VectorClock.from_dict({"r1":2}),"r2":VectorClock.from_dict({"r2":2}),"r3":VectorClock.from_dict({"r1":2})}
    clock=VectorClock.from_dict({"r1":2,"r2":2,"r3":2}); return {"r1":clock,"r2":clock,"r3":clock}

def deps(standing="ALIVE"): return DependencyGraph(edges={SUBJECT:(DEP,),DEP:()},standings={DEP:standing})
