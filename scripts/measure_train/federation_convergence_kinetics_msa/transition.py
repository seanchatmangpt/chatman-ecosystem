from fractions import Fraction

STATES = ("ACTIVE", "FIXED", "REGRESSED", "BLOCKED")

def transition_kernel(episodes):
    counts = {source: {target: 0 for target in STATES} for source in STATES}
    for episode in episodes:
        for left, right in zip(episode.observations, episode.observations[1:]):
            counts[left.state][right.state] += 1
    kernel = {}
    for source in STATES:
        total = sum(counts[source].values())
        if total == 0:
            kernel[source] = {target: Fraction(int(target == source)) for target in STATES}
        else:
            kernel[source] = {target: Fraction(counts[source][target], total) for target in STATES}
    return kernel
