def standing(coverage,loss_calibration,witness_calibration,methodology_complete,dependencies=(),min_support=5,min_coverage=0.8,max_mae=0.2):
    deps=set(dependencies)
    if "BUILD_BROKEN" in deps: return "BUILD_BROKEN"
    if "BLOCKED" in deps: return "BLOCKED"
    if coverage.support<min_support or loss_calibration.support<min_support: return "UNKNOWN"
    if not methodology_complete: return "UNKNOWN"
    if float(coverage.rate)<min_coverage or float(loss_calibration.mae)>max_mae: return "UNSUPPORTED"
    if witness_calibration.support<min_support: return "UNKNOWN"
    return "PARTIAL_ALIVE"
