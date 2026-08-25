def observe(rows):
 if not rows:return {'sensor':'worst_stratum','standing':'UNKNOWN'}
 worst=max(rows,key=lambda r:r.get('error_rate',0.0))
 return {'sensor':'worst_stratum','stratum':worst['stratum'],'error_rate':worst.get('error_rate',0.0)}
