"""Effective progress-state resolution shared by every reader of K-05 states.

``progress_topic_state`` is append-only: every answered task appends a new row.
Reading only the newest row is wrong for practice attempts — one wrong practice
answer would visibly erase a topic's achieved status, and a correct practice
would look like no change at all. The rule used everywhere:

* practice attempts can lift a topic (in_progress_practice -> partially_mastered)
  but never lower it — practice is not evidence of forgetting;
* verification attempts always win, even when they fail (a failed verification
  really does downgrade verified mastery).
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

PRACTICE = "in_progress_practice"
PARTIALLY_MASTERED = "partially_mastered"
VERIFIED_MASTERY = "verified_mastery"

STATUS_RANK = {PRACTICE: 1, PARTIALLY_MASTERED: 2, VERIFIED_MASTERY: 3}


def status_value(value: Any) -> str:
    """Enum (or raw column value) -> lowercase canonical string.

    SQLAlchemy's Enum columns persist the member *names* (``VERIFIED_MASTERY``)
    while the API serialises the enum *values* (``verified_mastery``), so every
    reader must normalise before comparing.
    """
    return str(getattr(value, "value", value)).strip().lower()


def resolve_effective_states(
    rows: Iterable[Any],
    *,
    key: Callable[[Any], Any],
) -> dict[Any, Any]:
    """Fold state history into the effective (displayed) state per key.

    ``rows`` must expose ``valid_from``, ``version``, ``kind`` and ``status``.
    Returns ``{key(row): row}``.
    """
    effective: dict[Any, Any] = {}
    for row in sorted(rows, key=lambda r: (r.valid_from, getattr(r, "version", 0) or 0)):
        k = key(row)
        prev = effective.get(k)
        if prev is None:
            effective[k] = row
            continue
        if status_value(row.kind) == "verified":
            effective[k] = row
            continue
        if STATUS_RANK.get(status_value(row.status), 0) > STATUS_RANK.get(status_value(prev.status), 0):
            effective[k] = row
    return effective
