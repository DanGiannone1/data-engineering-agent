"""Azure OpenAI client setup using DefaultAzureCredential."""

import os
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider


def get_openai_client() -> AzureOpenAI:
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(process_timeout=30),
        "https://cognitiveservices.azure.com/.default",
    )
    return AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        azure_ad_token_provider=token_provider,
        api_version="2024-10-21",
    )


def get_deployment() -> str:
    return os.environ["AZURE_OPENAI_DEPLOYMENT"]
