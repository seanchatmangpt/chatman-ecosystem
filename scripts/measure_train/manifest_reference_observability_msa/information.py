def uncertainty_reduction(before, after):
    return before.width-after.width

def information_efficiency(before, after, added_attempts):
    if added_attempts <= 0:
        raise ValueError("added_attempts must be positive")
    return uncertainty_reduction(before,after)/added_attempts
