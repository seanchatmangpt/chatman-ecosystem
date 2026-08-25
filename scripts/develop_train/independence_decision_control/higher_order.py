from fractions import Fraction


def interaction_excess(joint_entropy: Fraction, marginal_entropies):
    """Total-correlation style higher-order dependence witness."""
    value = sum(marginal_entropies, Fraction(0)) - joint_entropy
    return max(Fraction(0), value)
