def machine_record(qualification):
    return {
        "schema":"chatman.process-intelligence-crown-admission/1",
        "subject":qualification.subject.canonical,
        "standing":qualification.standing.value,
        "missing_obligations":list(qualification.census.missing),
        "failed_obligations":list(qualification.census.failures),
        "blockers":list(qualification.blockers),
        "rail_count":len(qualification.rails),
        "actuation_performed":False,
        "authority":"SELECT|CONSTRUCT|VERIFY",
    }
