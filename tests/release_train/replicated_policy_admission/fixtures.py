from datetime import datetime,timezone,timedelta
from scripts.release_train.replicated_policy_admission.subject import Subject
from scripts.release_train.replicated_policy_admission.vector_clock import VectorClock
from scripts.release_train.replicated_policy_admission.replica import ReplicaPolicyState
from scripts.release_train.replicated_policy_admission.lease import Lease
from scripts.release_train.replicated_policy_admission.policy import ExpectedPolicy
from scripts.release_train.replicated_policy_admission.dependency import DependencyGraph
SHA='0'*40; POL='a'*64; FRONT='b'*64; NOW=datetime(2026,8,23,0,30,tzinfo=timezone.utc)
def subject(): return Subject('seanchatmangpt/chatman-ecosystem',SHA)
def state(replica,gen=7,pol=POL,front=FRONT,clock=None): return ReplicaPolicyState(replica,subject(),gen,pol,front,VectorClock.from_dict(clock or {replica:1}))
def lease(): return Lease(NOW-timedelta(minutes=10),NOW+timedelta(minutes=10))
def expected(): return ExpectedPolicy(7,POL,FRONT)
def deps(status='PARTIAL_ALIVE'): return DependencyGraph((('policy','release'),),(('policy',status),('release','PARTIAL_ALIVE')))
