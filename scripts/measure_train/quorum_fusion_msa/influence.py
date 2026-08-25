from .fusion import fuse
def leave_one_out_influence(calibrations):
    if len(calibrations)<2: return ()
    full=fuse(calibrations)
    out=[]
    for i,c in enumerate(calibrations):
        rest=list(calibrations[:i])+list(calibrations[i+1:])
        reduced=fuse(rest)
        delta=sum(abs(a-b) for a,b in zip(full["center"],reduced["center"]))
        out.append((c.sensor_id,delta))
    return tuple(sorted(out))
