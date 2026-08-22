from datetime import datetime
from .intent import PromotionIntent
from .lease import IntentLease
from .frontier import PromotionFrontier
from .subject import Refusal


def admit_intent(intent: PromotionIntent, lease: IntentLease, frontier: PromotionFrontier, now: datetime) -> None:
    if not lease.active(now):
        raise Refusal('REFUSED[INTENT_LEASE_INACTIVE]')
    if intent.cut != frontier.cut:
        raise Refusal('REFUSED[STALE_PROMOTION_CUT]')
    if intent.strategy.fingerprint() != frontier.strategy_digest:
        raise Refusal('REFUSED[STALE_SELECTION_STRATEGY]')
    if intent.policy_digest != frontier.policy_digest:
        raise Refusal('REFUSED[STALE_PROMOTION_POLICY]')
