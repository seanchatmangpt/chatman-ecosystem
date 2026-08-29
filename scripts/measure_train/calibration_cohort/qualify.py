from .frontier import current_frontier
from .admission import admit_cohort
from .census import census
from .standing import standing
from .information import cohort_information
from .receipt import manufacture_receipt
from .telemetry import project
def qualify(subject, all_epochs, cohort, observations, parent_receipt=None, **admission):
    frontier=current_frontier(all_epochs)
    sync=admit_cohort(cohort,frontier,**admission)
    rows=census(cohort,observations)
    status=standing(rows)
    return {"frontier":frontier,"synchrony":sync,"information":cohort_information(sync,cohort.epochs),
            "census":rows,"standing":status,"receipt":manufacture_receipt(subject,cohort,sync,rows,status,parent_receipt),
            "telemetry":project(subject,cohort,sync,rows),"actuation_performed":False}
