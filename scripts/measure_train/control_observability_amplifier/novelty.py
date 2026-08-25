def observe(previous, current):
 p=set(previous); c=set(current); novel=sorted(c-p)
 return {'sensor':'novelty','novel':novel,'novelty_rate':len(novel)/len(c) if c else 0.0}
