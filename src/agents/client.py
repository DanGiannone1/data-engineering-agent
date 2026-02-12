"""Azure OpenAI client setup for MAF."""

import os
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential


def get_client() -> AzureOpenAIChatClient:
    """Create Azure OpenAI chat client with Azure AD auth."""
    return AzureOpenAIChatClient(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        credential=AzureCliCredential(process_timeout=60),
        api_version="2025-01-01-preview",
    )
