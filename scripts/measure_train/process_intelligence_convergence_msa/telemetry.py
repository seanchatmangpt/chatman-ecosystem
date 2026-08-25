def project(epochs, convergence, cut):
    events=[]
    for epoch in epochs:
        events.append({"activity":"process_closure_epoch","repo":epoch.subject.repo,"sha":epoch.subject.sha,"generation":epoch.subject.generation,"observed_at":epoch.observed_at.isoformat()})
    events.append({"activity":"process_closure_convergence","repo":epochs[-1].subject.repo,"sha":epochs[-1].subject.sha,"direction":convergence.direction,"blocking_cut":list(cut)})
    return tuple(events)
