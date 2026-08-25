def census(graph,validators,stats,calibration,robustness):
    return {
      "evidence_nodes":len(graph),"validators":len(tuple(validators)),"support":stats.support,
      "phi":stats.phi,"mutual_information":stats.mutual_information,
      "false_independent":str(calibration.false_independent),
      "max_ancestry_overlap":str(robustness.max_overlap),
      "max_information_inflation":str(robustness.max_inflation),
      "leave_one_out_flip_rate":str(robustness.leave_one_out_flip_rate),
    }
