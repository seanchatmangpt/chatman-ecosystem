from dataclasses import dataclass
from .ensemble import generalized_js
@dataclass(frozen=True)
class GainRealization:
    predicted_bits: float
    before_dispersion_bits: float
    after_dispersion_bits: float
    realized_bits: float
    error_bits: float
def realize_gain(predicted_bits,before_distributions,after_distributions):
    before=generalized_js(before_distributions); after=generalized_js(after_distributions)
    realized=max(0.0,before-after)
    return GainRealization(predicted_bits,before,after,realized,realized-predicted_bits)
