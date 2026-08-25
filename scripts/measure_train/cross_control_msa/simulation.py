from .refusal import Refused
def admit_simulation(rmse,providers,independent,collision,acyclic,current,max_rmse=.25):
 if rmse<0: raise Refused("REFUSED[INVALID_SIMULATION_RMSE]")
 if collision: raise Refused("REFUSED[IDEMPOTENCY_COLLISION]")
 if not acyclic: raise Refused("REFUSED[CYCLIC_TRACE]")
 if not current: raise Refused("REFUSED[STALE_SIMULATION_SEMANTICS]")
 if providers<2 or not independent: raise Refused("REFUSED[INSUFFICIENT_PROVIDER_INDEPENDENCE]")
 if rmse>max_rmse: raise Refused("REFUSED[SIMULATION_CALIBRATION_FAILURE]")
 return True
