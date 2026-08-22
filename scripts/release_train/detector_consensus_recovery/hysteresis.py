from dataclasses import dataclass

@dataclass(frozen=True)
class HysteresisState:
    regime: str="STABLE"
    enter_streak: int=0
    clear_streak: int=0

def advance(state, consensus, enter_required=2, clear_required=3):
    if consensus.verdict=="FAIL": return HysteresisState("FAILED",0,0)
    if consensus.verdict=="DRIFT_CONFIRMED":
        n=state.enter_streak+1
        return HysteresisState("DRIFT" if n>=enter_required else "SUSPECT",n,0)
    if consensus.verdict=="STABLE_CONFIRMED":
        c=state.clear_streak+1
        if state.regime in {"DRIFT","SUSPECT"} and c<clear_required: return HysteresisState(state.regime,0,c)
        return HysteresisState("STABLE",0,c)
    return HysteresisState(state.regime,0,0)
