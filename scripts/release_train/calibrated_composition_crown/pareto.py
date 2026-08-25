def dominates(a,b):
    better=(a.coverage>=b.coverage and a.mean_width<=b.mean_width and a.miss_rate<=b.miss_rate)
    strict=(a.coverage>b.coverage or a.mean_width<b.mean_width or a.miss_rate<b.miss_rate)
    return better and strict
def frontier(candidates):
    c=list(candidates)
    return tuple(x for x in c if not any(y is not x and dominates(y,x) for y in c))
