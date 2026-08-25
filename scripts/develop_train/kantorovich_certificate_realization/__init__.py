"""Empirical realization capital for proof-bearing Kantorovich certificates."""
from .errors import Refused
from .subject import Subject
from .certificate import Certificate
from .observation import Observation
from .admission import admit as admit_observations
from .feasibility import Feasibility, measure as measure_feasibility
from .oracle import OracleDifferential, differential
from .consequence import ConsequenceError, evaluate
from .independence import IndependenceWitness, witness
from .calibration import Calibration, calibrate
from .currentness import current
from .drift import Cusum
from .strata import group, worst_stratum
from .methodologies import REQUIRED, require_complete as require_methodologies
from .failures import World, require_complete as require_failure_worlds
from .authority import Action, admit as admit_action
from .receipt import Receipt
from .replay import replay
from .qualification import Qualification, qualify
