def observe(seed_count, opportunities):
 e=(len(opportunities)/seed_count) if seed_count else 0.0
 return {'sensor':'opportunity_multiplier','seeds':seed_count,'opportunities':len(opportunities),'E':e}
