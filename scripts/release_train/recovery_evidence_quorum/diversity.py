def effective_source_diversity(clusters):
    sizes=[len(cluster) for cluster in clusters]
    total=sum(sizes)
    if total==0:
        return (0,1)
    denominator=sum(size*size for size in sizes)
    return (total*total,denominator)
