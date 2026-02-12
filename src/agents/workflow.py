"""MAF Workflow for Fund Transactions transformation with HITL review."""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Callable

from agent_framework import Agent

from .client import get_client
from .tools import (
    read_fund_transactions_mapping,
    read_a_type_lookup,
    read_t_type_lookup,
    read_reversal_codes,
    read_source_data_sample,
    list_source_columns,
    get_data_profile,
)
from .models import StructuredPseudocode, GeneratedCode


# =============================================================================
# Session State
# =============================================================================

class Phase(str, Enum):
    STARTING = "starting"
    PROFILING = "profiling"
    PSEUDOCODE_REVIEW = "pseudocode_review"
    CODE_GENERATION = "code_generation"
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
    """Transformation session with HITL support."""
    id: str
    status: Status = Status.PENDING
    phase: Phase = Phase.STARTING
    messages: list[Message] = field(default_factory=list)
    pseudocode: Optional[dict] = None
    pyspark_code: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # HITL state
    awaiting_review: bool = False
    _review_event: Optional[asyncio.Event] = field(default=None, repr=False)
    review_response: Optional[dict] = None

    def log(self, role: str, content: str, phase: Optional[str] = None) -> Message:
        msg = Message.create(role, content, phase or self.phase.value)
        self.messages.append(msg)
        return msg

    async def wait_for_review(self):
        """Block until review is submitted."""
        self._review_event = asyncio.Event()
        await self._review_event.wait()
        self._review_event = None

    def submit_review(self, approved: bool, feedback: str = ""):
        """Submit review response and unblock workflow."""
        self.review_response = {"approved": approved, "feedback": feedback}
        if self._review_event:
            self._review_event.set()


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


# Global store
store = SessionStore()


# =============================================================================
# Agent Definitions
# =============================================================================

PROFILER_INSTRUCTIONS = """You are a data engineering agent analyzing Fund Transactions data.

Your task is to generate a STRUCTURED transformation plan as JSON that auditors can review.

## Tools Available
- read_fund_transactions_mapping() - DNAV field mappings
- read_a_type_lookup() - Asset type lookup (Client -> DNAV)
- read_t_type_lookup() - Transaction type lookup (Client -> DNAV)
- read_reversal_codes() - Cancellation/reversal codes
- read_source_data_sample() - Sample source rows
- list_source_columns() - List all source columns
- get_data_profile() - Statistical profile of source data

## Output Format
Return a JSON object with this EXACT structure:
{
  "version": 1,
  "summary": "Brief description of the transformation",
  "steps": [
    // Use these step types:

    // 1. field_mapping - direct column mappings
    {"id": "1", "type": "field_mapping", "title": "...", "mappings": [
      {"source": "Col_A", "target": "DNAV_A", "transform": "direct"}
    ]},

    // 2. lookup_join - join with lookup tables
    {"id": "2", "type": "lookup_join", "title": "...",
     "join_key": {"source": "Category", "lookup": "Client_A_TYPE"},
     "output_field": "DNAV_A_TYPE", "filter": "Exclude CSH, N/A"},

    // 3. business_rule - conditional logic
    {"id": "3", "type": "business_rule", "title": "...", "rules": [
      {"condition": "T_TYPE = DT_SELL", "action": "T_AMOUNT = -ABS(amount)"}
    ]},

    // 4. filter - row filtering
    {"id": "4", "type": "filter", "title": "...", "condition": "A_TYPE != 'CSH'"},

    // 5. calculation - derived fields
    {"id": "5", "type": "calculation", "title": "...", "output_field": "NAV", "formula": "..."},

    // 6. output - final output
    {"id": "6", "type": "output", "title": "Write output", "format": "parquet", "destination": "DNAV Fund Transactions"}
  ]
}

## Process
1. Read all lookup tables and mappings first
2. Sample source data to understand column names
3. Generate comprehensive transformation steps
4. Use clear, non-technical language for auditors

Return ONLY valid JSON, no markdown or explanatory text."""


CODE_GENERATOR_INSTRUCTIONS = """You are a PySpark code generation agent.

Generate production-ready PySpark code from the approved transformation plan.

Requirements:
- Use PySpark DataFrame API
- Include proper error handling
- Handle nulls and edge cases
- Code should be self-contained (create SparkSession)
- Add comments explaining each transformation step

Return ONLY the Python code, no markdown or explanations."""


def create_profiler_agent() -> Agent:
    """Create the profiler agent that generates structured pseudocode."""
    client = get_client()
    return Agent(
        client=client,
        name="FundTransactionsProfiler",
        instructions=PROFILER_INSTRUCTIONS,
        tools=[
            read_fund_transactions_mapping,
            read_a_type_lookup,
            read_t_type_lookup,
            read_reversal_codes,
            read_source_data_sample,
            list_source_columns,
            get_data_profile,
        ],
    )


def create_code_generator_agent() -> Agent:
    """Create the code generator agent."""
    client = get_client()
    return Agent(
        client=client,
        name="PySparkCodeGenerator",
        instructions=CODE_GENERATOR_INSTRUCTIONS,
        tools=[],  # No tools needed, just generates code from pseudocode
    )


# =============================================================================
# Workflow
# =============================================================================

async def run_workflow(session: Session, on_update: Optional[Callable] = None):
    """
    Run the Fund Transactions transformation workflow.

    Phases:
    1. Profiling - Analyze data and generate structured pseudocode
    2. Pseudocode Review - HITL checkpoint for auditor review
    3. Code Generation - Generate PySpark from approved pseudocode
    4. Output Review - HITL checkpoint for final approval
    """
    def notify():
        if on_update:
            on_update(session)

    try:
        session.status = Status.RUNNING
        notify()

        # Phase 1: Profiling
        session.phase = Phase.PROFILING
        session.log("agent", "Analyzing Fund Transactions data and generating transformation plan...")
        notify()

        profiler = create_profiler_agent()
        thread = profiler.get_new_thread()

        response = await profiler.run(
            "Analyze the Fund Transactions data and generate a structured transformation plan. "
            "Read all the lookup tables, sample the source data, then create the pseudocode JSON.",
            thread=thread,
        )

        # Extract JSON from response
        response_text = response.text if hasattr(response, "text") else str(response)

        # Try to parse as JSON
        try:
            # Handle markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            session.pseudocode = json.loads(response_text.strip())
        except json.JSONDecodeError:
            # If parsing fails, create a minimal structure
            session.pseudocode = {
                "version": 1,
                "summary": "Transformation plan (parsing error - see raw text)",
                "steps": [],
                "raw_text": response_text,
            }

        # Phase 2: Pseudocode Review (HITL)
        session.phase = Phase.PSEUDOCODE_REVIEW
        session.log("agent", json.dumps(session.pseudocode))
        session.awaiting_review = True
        notify()

        # Wait for auditor review
        await session.wait_for_review()

        # Handle revision loop
        while not session.review_response.get("approved", False):
            feedback = session.review_response.get("feedback", "")
            session.log("auditor", f"Feedback: {feedback}")
            session.awaiting_review = False
            notify()

            session.log("agent", "Revising transformation plan based on feedback...")
            notify()

            # Ask profiler to revise
            revision_response = await profiler.run(
                f"Revise the transformation plan based on this feedback:\n\n{feedback}\n\n"
                f"Current plan:\n{json.dumps(session.pseudocode, indent=2)}\n\n"
                "Increment the version number and return the updated JSON.",
                thread=thread,
            )

            revision_text = revision_response.text if hasattr(revision_response, "text") else str(revision_response)

            try:
                if "```json" in revision_text:
                    revision_text = revision_text.split("```json")[1].split("```")[0]
                elif "```" in revision_text:
                    revision_text = revision_text.split("```")[1].split("```")[0]

                session.pseudocode = json.loads(revision_text.strip())
            except json.JSONDecodeError:
                session.pseudocode["version"] = session.pseudocode.get("version", 1) + 1
                session.pseudocode["raw_text"] = revision_text

            session.log("agent", json.dumps(session.pseudocode))
            session.review_response = None
            session.awaiting_review = True
            notify()

            await session.wait_for_review()

        session.log("auditor", "Approved")
        session.awaiting_review = False
        notify()

        # Phase 3: Code Generation
        session.phase = Phase.CODE_GENERATION
        session.log("agent", "Generating PySpark code from approved transformation plan...")
        notify()

        code_generator = create_code_generator_agent()
        code_thread = code_generator.get_new_thread()

        code_response = await code_generator.run(
            f"Generate PySpark code for this transformation plan:\n\n"
            f"{json.dumps(session.pseudocode, indent=2)}\n\n"
            "Input file: input_data/Effective_Transactions_sample.csv\n"
            "Output: output/fund_transactions.parquet",
            thread=code_thread,
        )

        session.pyspark_code = code_response.text if hasattr(code_response, "text") else str(code_response)
        session.log("agent", f"Generated PySpark code ({len(session.pyspark_code)} characters)")
        session.log("agent", f"```python\n{session.pyspark_code[:1500]}...\n```")
        notify()

        # Phase 4: Output Review (HITL)
        session.phase = Phase.OUTPUT_REVIEW
        session.log("agent", "Transformation code ready for review.")
        session.awaiting_review = True
        notify()

        await session.wait_for_review()

        if session.review_response.get("approved", False):
            session.log("auditor", "Approved")
            session.phase = Phase.COMPLETED
            session.status = Status.COMPLETED
            session.log("agent", "Transformation workflow complete!")
        else:
            session.log("auditor", f"Rejected: {session.review_response.get('feedback', '')}")
            session.phase = Phase.COMPLETED
            session.status = Status.COMPLETED

        session.awaiting_review = False
        notify()

    except Exception as e:
        session.phase = Phase.FAILED
        session.status = Status.FAILED
        session.log("agent", f"Error: {str(e)}")
        notify()
        raise


def start_workflow_async(session: Session, on_update: Optional[Callable] = None):
    """Start the workflow in a background task."""
    loop = asyncio.new_event_loop()

    def run_in_thread():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_workflow(session, on_update))

    import threading
    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    return thread
