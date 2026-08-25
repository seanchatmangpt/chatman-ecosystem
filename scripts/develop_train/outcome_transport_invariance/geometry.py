from math import sqrt, log

def tv(source, target):
    s, t = source.data(), target.data()
    return 0.5 * sum(abs(s.get(k, 0) - t.get(k, 0)) for k in set(s) | set(t))

def hellinger(source, target):
    s, t = source.data(), target.data()
    return sqrt(0.5 * sum((sqrt(s.get(k, 0)) - sqrt(t.get(k, 0))) ** 2 for k in set(s) | set(t)))

def js(source, target):
    s, t = source.data(), target.data()
    cells = set(s) | set(t)
    midpoint = {k: (s.get(k, 0) + t.get(k, 0)) / 2 for k in cells}
    def kl(p):
        return sum(p.get(k, 0) * log(p.get(k, 0) / midpoint[k]) for k in cells if p.get(k, 0) > 0)
    return 0.5 * (kl(s) + kl(t))
