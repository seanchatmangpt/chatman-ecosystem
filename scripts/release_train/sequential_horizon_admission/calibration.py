from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
from .rational import nonnegative,unit
@dataclass(frozen=True)
class GainCalibration:
    support:int; mae_bits:Fraction; reliability:Fraction; cusum:Fraction; cusum_limit:Fraction
    def __post_init__(self):
        if self.support<0: raise Refused("INVALID_SUPPORT")
        object.__setattr__(self,"mae_bits",nonnegative(self.mae_bits)); object.__setattr__(self,"reliability",unit(self.reliability)); object.__setattr__(self,"cusum",nonnegative(self.cusum)); object.__setattr__(self,"cusum_limit",nonnegative(self.cusum_limit))
    def admit(self,*,min_support=4,min_reliability=Fraction(3,4)):
        if self.support<min_support: raise Refused("UNDER_SUPPORTED_GAIN_MODEL")
        if self.reliability<min_reliability: raise Refused("UNRELIABLE_GAIN_MODEL")
        if self.cusum>self.cusum_limit: raise Refused("GAIN_MODEL_DRIFT")
        return self
