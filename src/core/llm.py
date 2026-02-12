"""LLM client for Azure OpenAI."""

import os
import json
import re
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure OpenAI configuration - use Azure AD authentication
_credential = DefaultAzureCredential()
_token_provider = get_bearer_token_provider(_credential, "https://cognitiveservices.azure.com/.default")

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-02-15-preview",
    azure_ad_token_provider=_token_provider,
)

DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")


def chat(system_prompt: str, user_message: str, json_mode: bool = False) -> str:
    """Send a chat completion request."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    kwargs = {
        "model": DEPLOYMENT,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 8000,
    }

    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    text = text.strip()

    # Remove markdown code blocks if present
    if text.startswith("```"):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)

    return json.loads(text.strip())
