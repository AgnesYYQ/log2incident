from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

class RawLog(BaseModel):
    id: str
    timestamp: datetime
    source: str
    message: str
    trace_id: Optional[str] = None
    metadata: Optional[Dict] = {}

class TaggedLog(RawLog):
    tags: List[str] = []

class Event(BaseModel):
    id: str
    timestamp: datetime
    log_id: str
    type: str
    severity: str
    description: str
    trace_id: Optional[str] = None

class Incident(BaseModel):
    id: str
    timestamp: datetime
    events: List[str]  # event ids
    status: str  # open, closed, etc.
    summary: str
    trace_id: Optional[str] = None