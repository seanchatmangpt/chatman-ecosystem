"""Release closure court: fail-closed evaluation of a semantic release closure set.

The closure file (e.g. ``release/v26.9.24/closure.json``) is the executable projection of the
normative release ledger (engineering-standards RFC-0002). This court answers "what remains for
the release?" deterministically: every row must be terminal, bound to an exact subject, and free
of the typed defects listed in ``court.RULES``.
"""
