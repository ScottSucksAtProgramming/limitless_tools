"""
Typed models should parse lifelog and content nodes correctly.
Single assert per test.
"""


def test_lifelog_model_parses_minimal_dict():
    from limitless_tools.models.lifelog import Lifelog

    data = {
        "id": "m1",
        "title": "Title",
        "markdown": None,
        "contents": [
            {"type": "paragraph", "content": "hello", "children": []}
        ],
        "startTime": "2025-01-01T00:00:00Z",
        "endTime": "2025-01-01T01:00:00Z",
        "isStarred": False,
        "updatedAt": "2025-01-01T02:00:00Z",
    }
    ll = Lifelog.model_validate(data)
    assert ll.id == "m1"

