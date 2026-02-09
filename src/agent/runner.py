"""Agent runner — calls Azure OpenAI with a system prompt and returns the result."""

import json
import logging
from agent.client import get_openai_client, get_deployment

logger = logging.getLogger(__name__)


def run_agent(system_prompt: str, user_message: str) -> str:
    """Run an agent call with a system prompt and user message.

    Returns the assistant's response text.
    """
    client = get_openai_client()
    deployment = get_deployment()

    logger.info("Calling Azure OpenAI (deployment=%s)", deployment)

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
    )

    result = response.choices[0].message.content
    logger.info(
        "LLM response: %d chars, %d prompt tokens, %d completion tokens",
        len(result),
        response.usage.prompt_tokens,
        response.usage.completion_tokens,
    )
    return result


def run_agent_code(system_prompt: str, user_message: str) -> str:
    """Run agent and extract clean Python code from the response."""
    result = run_agent(system_prompt, user_message)
    text = result.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove opening fence (```python or ```)
        lines = lines[1:]
        # Remove closing fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    # Strip any leading non-code text (lines before the first import/from/# comment)
    final_lines = text.split("\n")
    start_idx = 0
    for i, line in enumerate(final_lines):
        stripped = line.strip()
        if stripped.startswith(("import ", "from ", "#", "\"\"\"", "'''")) or stripped == "":
            start_idx = i
            break

    return "\n".join(final_lines[start_idx:])


def run_agent_json(system_prompt: str, user_message: str) -> dict:
    """Run agent and parse the response as JSON."""
    result = run_agent(system_prompt, user_message)

    # Try to extract JSON from the response (handle markdown code blocks)
    text = result.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (```json and ```)
        text = "\n".join(lines[1:-1])

    return json.loads(text)
