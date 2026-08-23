from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.release_train.feedback_policy_admission.subject import Subject
from scripts.release_train.feedback_policy_admission.policy import PolicyIdentity,FeedbackStrategy
from scripts.release_train.feedback_policy_admission.realization import StepRealization
SHA="a"*40
PD="b"*64
def subject(): return Subject("seanchatmangpt/chatman-ecosystem",SHA)
def policy(g=1,d=PD,s=FeedbackStrategy.HOLD): return PolicyIdentity("release",g,d,s)
def steps(residuals=(0,0,0)):
    t=datetime(2026,8,23,4,0,tzinfo=timezone.utc)
    return tuple(StepRealization(i,f"e{i}",Fraction(1,5),Fraction(1,5)+Fraction(r),1,1,1,t+timedelta(minutes=i)) for i,r in enumerate(residuals))
