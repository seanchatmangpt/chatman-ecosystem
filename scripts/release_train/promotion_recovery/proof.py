from dataclasses import dataclass
from .subject import Refusal

@dataclass(frozen=True)
class SelectionProof:
    selected_cut_id: str
    policy_digest: str
    frontier_digest: str
    def admit(self, policy, frontier):
        if self.policy_digest != policy.digest: raise Refusal('REFUSED[STALE_SELECTION_POLICY]')
        if self.frontier_digest != frontier.digest: raise Refusal('REFUSED[STALE_CANDIDATE_FRONTIER]')
        actual=frontier.select(policy.strategy).cut_id
        if self.selected_cut_id != actual: raise Refusal('REFUSED[NON_REPRODUCIBLE_SELECTION]')
        return True
