def observe(opportunities):
 actionable=[o for o in opportunities if o.get('exact_subject') and o.get('falsifier')]
 return {'sensor':'actionability','actionable':len(actionable),'total':len(opportunities),'rate':len(actionable)/len(opportunities) if opportunities else 0.0}
