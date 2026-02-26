from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class ConversationMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    thread_id: str
    client_id: str
    role: str  # "agent" or "auditor"
    content: str
    phase: str  # "change_detection", "pseudocode_review", "code_generation", "output_review"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
