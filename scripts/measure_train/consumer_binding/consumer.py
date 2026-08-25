from dataclasses import dataclass
from .subject import Subject, Refused

@dataclass(frozen=True, order=True)
class Consumer:
    subject: Subject
    component: str

    def __post_init__(self):
        if not self.component.strip():
            raise Refused("REFUSED[EMPTY_CONSUMER_COMPONENT]")
