from statistics import median
from .distribution import normalized_error_vector,jensen_shannon
from .subject import Refused
def fuse(calibrations, min_support=5, max_js=0.25):
    if not calibrations: raise Refused("REFUSED[EMPTY_CALIBRATION_SET]")
    if any(c.support < min_support for c in calibrations):
        raise Refused("REFUSED[UNDER_SUPPORTED_SENSOR]")
    vectors=[normalized_error_vector(c) for c in calibrations]
    center=tuple(median(v[i] for v in vectors) for i in range(4))
    s=sum(center); center=tuple(v/s for v in center)
    js=[jensen_shannon(v,center) for v in vectors]
    state="DIVERGED" if any(x>max_js for x in js) else "COHERENT"
    return {"center":center,"js":tuple(js),"state":state}
