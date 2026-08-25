from fractions import Fraction

def coverage(observations, required_transports):
    required = set(required_transports)
    seen = {row.transport_id for row in observations}
    return Fraction(len(required & seen), len(required)) if required else Fraction(1)
