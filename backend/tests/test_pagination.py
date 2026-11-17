from __future__ import annotations

from app.core.api import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT, Page, paginated


def test_pagination_limits_are_bounded():
    assert DEFAULT_PAGE_LIMIT == 50
    assert MAX_PAGE_LIMIT == 200


def test_paginated_envelope_and_window():
    items = [{"id": index} for index in range(5)]
    body = paginated(items, Page(limit=2, offset=1))
    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert body["items"] == [{"id": 1}, {"id": 2}]
    empty = paginated(items, Page(limit=10, offset=10))
    assert empty["items"] == []
    assert empty["total"] == 5
