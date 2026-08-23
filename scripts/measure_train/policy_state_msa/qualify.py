from .history import admit_history
from .linearization import cas_linearization
from .conflict import classify_conflicts
from .temporal import monitor_trace
from .frontier import current_frontier
from .metrics import measure
from .calibration import calibrate
from .durability import durability_state
from .census import census
from .receipt import manufacture_receipt
from .telemetry import project

def qualify(subject,transitions,restart_witness,fault_trials,parent_receipt=None):
    rows=admit_history(subject,transitions); cas_linearization(rows)
    conflicts=classify_conflicts(rows); temporal=monitor_trace(rows); frontier=current_frontier([x.after for x in rows if x.after])
    metrics=measure(rows); calibration=calibrate(fault_trials); durability=durability_state(restart_witness)
    summary=census(rows,conflicts,temporal,durability,calibration)
    summary.update({"commits":metrics.commits,"refusals":metrics.refusals,"commit_yield":metrics.commit_yield,"wilson_lower":calibration.wilson_lower})
    receipt=manufacture_receipt(subject,frontier,summary,parent_receipt)
    return {"frontier":frontier,"census":summary,"receipt":receipt,"telemetry":project(subject,rows,conflicts),"standing":summary["standing"],"actuation_performed":False}
