from .admission import admit
from .correspondence import result_correspondence
from .independence import require_independence
from .capital import effective_capital
from .standing import standing
from .receipt import manufacture
def qualify(subject,rows,calibration,now):
 rows=admit(subject,rows,now); result=result_correspondence(rows); require_independence(rows); cap=effective_capital(rows); status=standing(rows,calibration,cap)
 return {"standing":status,"result_digest":result,"effective_capital":cap,"receipt":None if status in {"BUILD_BROKEN","REFUSED"} else manufacture(subject,result,cap,status),"actuation_performed":False}
