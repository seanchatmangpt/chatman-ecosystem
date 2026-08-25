from dataclasses import dataclass
@dataclass(frozen=True)
class RuntimeEvidence:
    subject_sha:str; executed:bool; exit_code:int|None; postcondition:bool|None
    @property
    def standing(self):
        if not self.executed: return "UNKNOWN"
        if self.exit_code != 0: return "BUILD_BROKEN"
        if self.postcondition is not True: return "PARTIAL_ALIVE"
        return "PARTIAL_ALIVE"
