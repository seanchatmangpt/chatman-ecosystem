def observe(paths, exercised):
 missing=sorted(set(paths)-set(exercised))
 return {"sensor":"unexercised_path","missing":missing,"coverage":0 if not paths else (len(set(paths)&set(exercised))/len(set(paths)))}
