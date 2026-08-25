def project(subject,census,bounds,coverage,standing_value):
    events=[{
      "activity":"manifest_reference_observability",
      "repo":subject.repo,
      "sha":subject.sha,
      "standing":standing_value,
      "lower":str(bounds.lower),
      "upper":str(bounds.upper),
      "exact_fraction":str(coverage.exact_fraction),
      "observable_fraction":str(coverage.observable_fraction),
    }]
    for cid,required,state,attempts in census:
        events.append({"activity":"component_ref_census","component_id":cid,"required":required,"state":state,"attempts":attempts})
    return tuple(events)
