"""Release scorecard: deterministic metrics over git archives of the pinned release SHAs.

Two stages, split on the network/process boundary:

* ``observe`` (``scripts/observe_scorecard.py`` applying ``measure.py``) streams ``git archive <sha>`` of every pinned
  repository of the release and of its predecessor out of the local object databases (no
  extraction to disk, no network) and writes ``release/<v>/hardening/inputs/scorecard-observations.json``.
  Re-running it on the same pins is byte-identical (``--check``).
* ``project`` (``project.py``, pure, stdlib, no process or network) turns the committed
  observation plus the committed hardening inputs into ``scorecard.json`` and
  ``benchmark.json``; ``root_crown.hardening`` calls it and ``--check`` guards the bytes.
"""
