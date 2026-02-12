"""In-memory state management for transformation sessions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class Phase(str, Enum):
    STARTING = "starting"
    PROFILING = "profiling"
    PSEUDOCODE_REVIEW = "pseudocode_review"
    CODE_GENERATION = "code_generation"
    EXECUTION = "execution"
    OUTPUT_REVIEW = "output_review"
    COMPLETED = "completed"
    FAILED = "failed"


class Status(str, Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


@dataclass
class Message:
    id: str
    role: str  # "agent" or "auditor"
    content: str
    phase: str
    timestamp: str

    @classmethod
    def create(cls, role: str, content: str, phase: str) -> "Message":
        return cls(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            phase=phase,
            timestamp=datetime.utcnow().isoformat(),
        )


@dataclass
class Session:
    """A transformation session."""
    id: str
    status: Status = Status.PENDING
    phase: Phase = Phase.STARTING
    messages: list[Message] = field(default_factory=list)
    pseudocode: Optional[dict] = None
    pseudocode_version: int = 1
    pyspark_code: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Review state
    awaiting_review: bool = False
    review_event: Optional[object] = None  # threading.Event for blocking
    review_response: Optional[dict] = None

    def log(self, role: str, content: str, phase: Optional[str] = None):
        """Add a message to the session."""
        msg = Message.create(role, content, phase or self.phase.value)
        self.messages.append(msg)
        return msg


class SessionStore:
    """In-memory session storage."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create(self) -> Session:
        session_id = str(uuid.uuid4())
        session = Session(id=session_id)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def all(self) -> list[Session]:
        return list(self._sessions.values())


# Global store
store = SessionStore()
