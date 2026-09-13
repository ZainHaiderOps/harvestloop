"""Loads the small curated agronomy rulebook shipped as package data.

This is hand-written, illustrative guidance for this project — not a
verbatim copy of any real extension service's material — clearly labeled
as such in each rule's `source` field. It becomes the Checking agent's
ground truth in later phases, and the Search agent's first real
retrieval corpus in Phase 03.
"""

from __future__ import annotations

import json
from pathlib import Path

from harvest_loop.data.models import AgronomyRule

RULEBOOK_PATH = Path(__file__).parent / "agronomy_rulebook.json"


def load_rulebook() -> list[AgronomyRule]:
    raw = json.loads(RULEBOOK_PATH.read_text())
    return [AgronomyRule.model_validate(item) for item in raw]
