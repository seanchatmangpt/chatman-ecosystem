"""Pytest configuration: make sibling modules under prototype/ importable.

Inserts /Users/sac/chatman-ecosystem/prototype onto sys.path so that
composition, jurisdiction, verifier, and compound import cleanly from
tests/ without any package installation step.
"""

import os
import sys

PROTOTYPE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if PROTOTYPE_DIR not in sys.path:
    sys.path.insert(0, PROTOTYPE_DIR)
