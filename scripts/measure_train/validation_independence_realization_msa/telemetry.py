def project(subject,model,census_value,standing_value):
    return ({"activity":"validation_independence_measured","repo":subject.repo,"sha":subject.sha,
             "generation":model.generation,"standing":standing_value,**census_value},)
