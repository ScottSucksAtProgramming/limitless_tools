from __future__ import annotations

# ruff: noqa: UP006,UP035,UP037,UP045
from typing import List, Optional

from pydantic import BaseModel as PydanticBaseModel, Field


class ContentNode(PydanticBaseModel):
    type: Optional[str] = None
    content: Optional[str] = None
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    startOffsetMs: Optional[int] = None
    endOffsetMs: Optional[int] = None
    children: List['ContentNode'] = Field(default_factory=list)
    speakerName: Optional[str] = None
    speakerIdentifier: Optional[str] = None


class Lifelog(PydanticBaseModel):
    id: str
    title: Optional[str] = None
    markdown: Optional[str] = None
    contents: Optional[List[ContentNode]] = None
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    isStarred: Optional[bool] = None
    updatedAt: Optional[str] = None
