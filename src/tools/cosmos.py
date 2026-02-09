"""Cosmos DB conversation tools for the chat UI."""

from models.conversation import ConversationMessage
from clients.cosmos import upsert_message, query_messages


def save_message(message: ConversationMessage) -> dict:
    """Save a conversation message to Cosmos DB."""
    doc = message.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    return upsert_message(doc)


def get_conversation_history(thread_id: str) -> list[dict]:
    """Get all messages for a thread, ordered by timestamp."""
    return query_messages(thread_id)
