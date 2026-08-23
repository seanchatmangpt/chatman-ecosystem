from dataclasses import dataclass
from .subject import Refused

@dataclass(frozen=True)
class OracleIndependence:
    left_impl:str
    right_impl:str
    left_model:str
    right_model:str
    def require(self):
        if self.left_impl==self.right_impl:
            raise Refused("REFUSED[SHARED_ORACLE_IMPLEMENTATION]")
        if self.left_model==self.right_model:
            raise Refused("REFUSED[SHARED_ORACLE_MODEL]")
        return True
