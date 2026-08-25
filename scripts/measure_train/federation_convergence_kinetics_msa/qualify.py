from .episode import admit_episode
from .first_passage import first_passage
from .capability import on_time_capability
from .calibration import calibrate
from .dependence import effective_episodes
from .frontier import current
from .methodology import require_methods
from .strata import worst_stratum
from .standing import standing
from .receipt import manufacture
from .refusal import Refused

def qualify(subject, episode_rows, models, deadline, target, dependency_states=()):
    episodes = tuple(admit_episode(rows) for rows in episode_rows)
    if any(episode.subject != subject for episode in episodes):
        raise Refused("FOREIGN_QUALIFICATION_SUBJECT")
    passages = tuple(first_passage(episode) for episode in episodes)
    capability = on_time_capability(passages, deadline, target, min_support=5)
    truth = {passage.episode_id: passage.event and passage.duration <= deadline for passage in passages}
    calibration = calibrate([episode.observations[0] for episode in episodes], truth, min_support=5)
    effective = effective_episodes(episodes)
    model = current(models)
    require_methods([row for episode in episodes for row in episode.observations])
    worst = worst_stratum(episodes)
    status = standing(capability.state, calibration.state, effective.effective, worst.terminal_failure, dependency_states)
    receipt = None if status in {"BUILD_BROKEN", "BLOCKED"} else manufacture(subject, model, status, capability, effective)
    telemetry = tuple({"activity": "convergence_episode", "repo": subject.repo, "sha": subject.sha, "episode_id": episode.episode_id, "terminal": episode.terminal_state, "duration": episode.duration} for episode in episodes)
    return {"standing": status, "passages": passages, "capability": capability, "calibration": calibration, "effective": effective, "current_model": model, "worst_stratum": worst, "receipt": receipt, "telemetry": telemetry, "actuation_performed": False}
