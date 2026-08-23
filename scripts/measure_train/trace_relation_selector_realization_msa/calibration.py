from dataclasses import dataclass
from fractions import Fraction
from .bounds import wilson_upper

@dataclass(frozen=True)
class SelectorCalibration:
    support: int
    mean_abs_error_ppm: Fraction
    exceedance_upper: float
    state: str

def calibrate(predicted_ppm, realized_binary, min_support=5, max_mae_ppm=200000, max_exceedance=0.5):
    pairs=tuple(zip(predicted_ppm,realized_binary))
    n=len(pairs)
    if n==0:
        return SelectorCalibration(0,Fraction(0),1.0,"INSUFFICIENT")
    mae=sum(abs(p-(1_000_000 if y else 0)) for p,y in pairs)/n
    exceed=sum(1 for p,y in pairs if y and p < 500_000)
    upper=wilson_upper(exceed,n)
    if n<min_support:
        state="INSUFFICIENT"
    elif mae>max_mae_ppm or upper>max_exceedance:
        state="UNRELIABLE"
    else:
        state="CALIBRATED"
    return SelectorCalibration(n,Fraction(round(mae),1),upper,state)
