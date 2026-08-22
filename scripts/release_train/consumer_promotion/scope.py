_RANK={"FOCUSED":0,"INTEGRATION":1,"REPOSITORY":2}
def covers(witness:str, required:str)->bool:
    try: return _RANK[witness] >= _RANK[required]
    except KeyError as exc: raise ValueError("REFUSED[INVALID_SCOPE]") from exc
