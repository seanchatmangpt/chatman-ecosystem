def observe(receipts):
 bad=[r.get('id','?') for r in receipts if r.get('authority')!='OBSERVE|VERIFY' or r.get('actuation_performed') is not False]
 return {"sensor":"receipt_integrity","invalid":sorted(bad),"standing":"ALIVE" if not bad else "REFUSED[RECEIPT_AUTHORITY_DRIFT]"}
