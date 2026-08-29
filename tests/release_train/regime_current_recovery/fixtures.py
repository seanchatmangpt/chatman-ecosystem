from datetime import datetime,timedelta,timezone
from scripts.release_train.regime_current_recovery.subject import Subject
from scripts.release_train.regime_current_recovery.window import CalibrationWindow
from scripts.release_train.regime_current_recovery.calibration import CalibrationTrial,fit_model
from scripts.release_train.regime_current_recovery.regime import CalibrationRegime,RegimeState
from scripts.release_train.regime_current_recovery.frontier import RegimeFrontier
from scripts.release_train.regime_current_recovery.admission import model_digest
from scripts.release_train.regime_current_recovery.evidence import EvidenceSource,RecoveryWitness

NOW=datetime(2026,8,22,20,0,tzinfo=timezone.utc)
SUBJECT=Subject('seanchatmangpt/chatman-ecosystem','2e9e6ff5733424eab88fe0aa4d9f0cfeec39c34d')
DEP=Subject('seanchatmangpt/gymact','00497ba9c408ffe10b5bd75f06d827b141d5652f')
def model(source_id='s1',errors=0):
    window=CalibrationWindow(NOW-timedelta(hours=1),NOW); truth=[1,1,1,1,0,0,0,0]; pred=[1,1,1,1,0,0,0,0]
    if errors>=1: pred[0]=0
    if errors>=2: pred[4]=1
    trials=[CalibrationTrial(SUBJECT,source_id,bool(t),bool(p),NOW-timedelta(minutes=50-i)) for i,(t,p) in enumerate(zip(truth,pred))]
    return fit_model(SUBJECT,source_id,window,trials)
def frontier(source_id='s1',generation=2,state=RegimeState.STABLE,errors=0):
    return RegimeFrontier(CalibrationRegime(model(source_id,errors),generation,state,'WINDOW_L1'),())
def witness(source_id='s1',source=None,generation=2,outcome='PASS',front=None):
    front=front or frontier(source_id,generation); source=source or EvidenceSource(source_id,f'run-{source_id}',f'artifact-{source_id}',f'family-{source_id}')
    return RecoveryWitness(SUBJECT,'attempt-1',source,source_id,outcome,NOW-timedelta(minutes=1),generation,model_digest(front))
