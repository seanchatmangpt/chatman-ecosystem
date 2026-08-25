def project(subject,model,status,metrics):
    return ({"activity":"decision_realization_transport","repo":subject.repo,"sha":subject.sha,
             "source":model.source,"target":model.target,"generation":model.generation,"standing":status,**metrics},)
