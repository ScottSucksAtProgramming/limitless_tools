"""
Pydantic model defaults: ensure no shared mutable defaults.
Single assert per test.
"""


def test_contentnode_children_not_shared():
    from limitless_tools.models.lifelog import ContentNode

    a = ContentNode()
    b = ContentNode()
    a.children.append(ContentNode(type="x"))
    assert len(b.children) == 0

