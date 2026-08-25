from dataclasses import dataclass

@dataclass(frozen=True, order=True)
class Passage:
    episode_id: str
    duration: int
    event: bool
    terminal: str

def first_passage(episode, target="FIXED"):
    start = episode.observations[0].step
    for row in episode.observations:
        if row.state == target:
            return Passage(episode.episode_id, row.step - start, True, target)
        if row.state in {"REGRESSED", "BLOCKED"}:
            return Passage(episode.episode_id, row.step - start, False, row.state)
    return Passage(episode.episode_id, episode.duration, False, "CENSORED")
