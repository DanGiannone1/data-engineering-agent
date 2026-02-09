import os
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient, ContainerProxy


def get_conversations_container() -> ContainerProxy:
    endpoint = os.environ["COSMOS_ENDPOINT"]
    database_name = os.environ.get("COSMOS_DATABASE", "agent-db")
    client = CosmosClient(url=endpoint, credential=DefaultAzureCredential())
    db = client.get_database_client(database_name)
    return db.get_container_client("conversations")


def upsert_message(message: dict) -> dict:
    container = get_conversations_container()
    return container.upsert_item(message)


def query_messages(thread_id: str) -> list[dict]:
    container = get_conversations_container()
    query = "SELECT * FROM c WHERE c.thread_id = @thread_id ORDER BY c.timestamp ASC"
    items = container.query_items(
        query=query,
        parameters=[{"name": "@thread_id", "value": thread_id}],
        partition_key=thread_id,
    )
    return list(items)
