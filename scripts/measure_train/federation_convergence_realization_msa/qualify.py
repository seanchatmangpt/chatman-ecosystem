from .trajectory import admit
from .calibration import calibrate
from .oscillation import signature
from .dwell import fixed_dwell_seconds
from .capital import effective
from .methodology import require_all
from .receipt import manufacture
def qualify(subject,rows,sources,methods,now,rho=0,min_dwell=0,dependencies=()):
    rows=admit(subject,rows,now); require_all(methods); cal=calibrate(rows); cap=effective(sources,rho)
    deps=set(dependencies)
    if 'BUILD_BROKEN' in deps or 'FAIL' in deps: status='BUILD_BROKEN'
    elif 'BLOCKED' in deps: status='BLOCKED'
    elif cal.state!='CALIBRATED' or signature(rows)['oscillating'] or rows[-1].state!='FIXED' or rows[-1].blocker_count or rows[-1].error_mass or fixed_dwell_seconds(rows)<min_dwell: status='UNKNOWN'
    else: status='PARTIAL_ALIVE'
    rec=None if status in {'BUILD_BROKEN','BLOCKED'} else manufacture(subject,cal,cap,status)
    return {'standing':status,'calibration':cal,'capital':cap,'receipt':rec,'actuation_performed':False}
