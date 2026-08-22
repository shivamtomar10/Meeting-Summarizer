"""Pydantic models describing the API's response shapes."""

from typing import List, Optional
from pydantic import BaseModel


class ActionItem(BaseModel):
    task: str
    owner: Optional[str] = "Unassigned"
    due: Optional[str] = None


class MeetingSummaryResponse(BaseModel):
    id: int
    filename: str
    created_at: str
    transcript: str
    summary: str
    key_decisions: List[str] = []
    action_items: List[ActionItem] = []


class MeetingListItem(BaseModel):
    id: int
    filename: str
    created_at: str
    summary: str


class HealthResponse(BaseModel):
    status: str