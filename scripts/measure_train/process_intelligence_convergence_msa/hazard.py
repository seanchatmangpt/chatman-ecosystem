from fractions import Fraction

def transition_hazards(epochs):
    discharge=regress=exposure=0
    for a,b in zip(epochs,epochs[1:]):
        amap={o.obligation_id:o.state for o in a.obligations}; bmap={o.obligation_id:o.state for o in b.obligations}
        for oid in set(amap)&set(bmap):
            exposure += 1
            if amap[oid] != "PASS" and bmap[oid] == "PASS": discharge += 1
            elif amap[oid] == "PASS" and bmap[oid] != "PASS": regress += 1
    if exposure == 0: return {"exposure":0,"discharge_hazard":Fraction(0),"regression_hazard":Fraction(0)}
    return {"exposure":exposure,"discharge_hazard":Fraction(discharge,exposure),"regression_hazard":Fraction(regress,exposure)}
