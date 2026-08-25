from enum import Enum
class Strategy(str,Enum):
    MAX_COVERAGE="MAX_COVERAGE"; MIN_WIDTH="MIN_WIDTH"; MINIMAX_MISS="MINIMAX_MISS"; INFORMATION_GAIN="INFORMATION_GAIN"
def select(candidates,strategy):
    c=list(candidates); strategy=Strategy(strategy)
    if not c: return None
    if strategy is Strategy.MAX_COVERAGE: return max(c,key=lambda x:(x.coverage,-x.mean_width,x.mode))
    if strategy is Strategy.MIN_WIDTH: return min(c,key=lambda x:(x.mean_width,-x.coverage,x.mode))
    if strategy is Strategy.MINIMAX_MISS: return min(c,key=lambda x:(x.miss_rate,x.mean_width,x.mode))
    return max(c,key=lambda x:((x.coverage*(1-x.mean_width)), -x.miss_rate, x.mode))
