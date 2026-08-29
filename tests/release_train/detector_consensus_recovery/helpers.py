from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.release_train.detector_consensus_recovery.subject import Subject
from scripts.release_train.detector_consensus_recovery.detector import DetectorIdentity
from scripts.release_train.detector_consensus_recovery.observation import DetectorObservation
from scripts.release_train.detector_consensus_recovery.calibration import calibrate
from scripts.release_train.detector_consensus_recovery.frontier import CalibrationGeneration
from scripts.release_train.detector_consensus_recovery.vote import DetectorVote
from scripts.release_train.detector_consensus_recovery.independence import IndependenceProof
S=Subject("seanchatmangpt/chatman-ecosystem","0"*40)
NOW=datetime(2026,8,22,21,30,tzinfo=timezone.utc)
def detector(name,family,domain): return DetectorIdentity(name,family,domain,(("threshold",2),))
def generation(d,gen=1,bad=False):
    obs=[]
    for i in range(8):
        expected=i>=4; detected=expected
        if bad and i==0: detected=True
        obs.append(DetectorObservation(S,d,f"c{i}",NOW+timedelta(seconds=i),expected,detected,1 if expected and detected else None))
    c=calibrate(obs,max_far=Fraction(0,1) if bad else Fraction(1,4))
    return CalibrationGeneration(d.fingerprint,gen,c,True)
def vote(d,g,verdict): return DetectorVote(S,d,g.generation,g.calibration.detector_fingerprint,verdict,900)
def proof(a,b): return IndependenceProof(a.fingerprint,b.fingerprint,True,"distinct family + runtime provenance")
