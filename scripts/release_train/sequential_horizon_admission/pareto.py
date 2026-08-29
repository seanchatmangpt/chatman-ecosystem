def frontier(candidates):
    xs=tuple(candidates)
    def dominates(a,b):
        no_worse=a.information>=b.information and a.independence>=b.independence and a.cost<=b.cost and a.latency<=b.latency
        better=a.information>b.information or a.independence>b.independence or a.cost<b.cost or a.latency<b.latency
        return no_worse and better
    return tuple(x for x in xs if not any(dominates(y,x) for y in xs if y is not x))
