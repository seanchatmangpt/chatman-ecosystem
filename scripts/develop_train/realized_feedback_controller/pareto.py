def frontier(items):
    def dominates(a,b):
        av=(a.calibration_error,a.regret,a.exploration_cost)
        bv=(b.calibration_error,b.regret,b.exploration_cost)
        return all(x<=y for x,y in zip(av,bv)) and any(x<y for x,y in zip(av,bv))
    return tuple(x for x in items if not any(y is not x and dominates(y,x) for y in items))
