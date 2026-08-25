def census(observations):
    return tuple((o.projection.projection_id,o.projection.methodology,o.projection.engine,o.state,o.oracle_label) for o in sorted(observations,key=lambda x:x.projection.projection_id))
