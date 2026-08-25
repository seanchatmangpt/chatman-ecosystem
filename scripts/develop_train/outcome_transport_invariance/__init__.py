"""Outcome-transport invariance: reusable evidence capital under bounded population stress."""
from .errors import Refused
from .subject import Subject
from .population import Population
from .support import Support, analyze, require as require_positivity
from .geometry import tv, hellinger, js
from .weights import Weights, make as importance_weights, require_ess
from .estimators import ht, sn, gap
from .perturb import Delta, apply
from .stress import Stress, erosion, shift
from .calibration import Calibration, current
from .currentness import Cusum, stable
from .strata import Stratum, worst
from .methodology import REQUIRED, require as require_methods
from .correspondence import Engine, Region, engines, regions
from .failures import World, require as require_failures
from .pareto import Candidate, frontier
from .authority import Action, admit
from .receipt import Receipt, replay
from .qualification import Qualification, qualify
