REQUIRED={"SEARCH","SEMANTIC","DISTRIBUTED","SIMULATION"}
def observe(families):
 s=set(families); missing=sorted(REQUIRED-s)
 return {"sensor":"control_family","present":sorted(s),"missing":missing,"standing":"ALIVE" if not missing else "UNKNOWN"}
