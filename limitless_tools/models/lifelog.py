from __future__ import annotations

from typing import List, Optional
try:
    from pydantic import BaseModel  # type: ignore
except Exception:  # pragma: no cover - allow tests without pydantic installed
    class BaseModel:  # type: ignore
        def __init__(self, **data):
            for k, v in data.items():
                setattr(self, k, v)

        @classmethod
        def model_validate(cls, data: dict):
            return cls(**data)


class ContentNode(BaseModel):
    type: Optional[str] = None
    content: Optional[str] = None
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    startOffsetMs: Optional[int] = None
    endOffsetMs: Optional[int] = None
    children: List["ContentNode"] = []
    speakerName: Optional[str] = None
    speakerIdentifier: Optional[str] = None


class Lifelog(BaseModel):
    id: str
    title: Optional[str] = None
    markdown: Optional[str] = None
    contents: Optional[List[ContentNode]] = None
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    isStarred: Optional[bool] = None
    updatedAt: Optional[str] = None
