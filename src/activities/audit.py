"""Cross-cutting: conversation logging and audit events."""

import logging
from models.conversation import ConversationMessage
from tools.cosmos import save_message, get_conversation_history

logger = logging.getLogger(__name__)


def log_agent_message(thread_id: str, client_id: str, phase: str, content: str) -> dict:
    """Save an agent message to conversation history."""
    msg = ConversationMessage(
        thread_id=thread_id,
        client_id=client_id,
        role="agent",
        content=content,
        phase=phase,
    )
    return save_message(msg)


def log_auditor_message(thread_id: str, client_id: str, phase: str, content: str) -> dict:
    """Save an auditor message to conversation history."""
    msg = ConversationMessage(
        thread_id=thread_id,
        client_id=client_id,
        role="auditor",
        content=content,
        phase=phase,
    )
    return save_message(msg)


def get_thread_messages(thread_id: str) -> list[dict]:
    """Retrieve full conversation history for a thread."""
    return get_conversation_history(thread_id)
