"""Main transformation pipeline - pure Python, platform agnostic."""

import json
import threading
from typing import Callable, Optional

from .state import Session, Phase, Status, store
from .files import read_transactions, read_mapping, sample_data, profile_data
from .llm import chat, extract_json
from .prompts import PSEUDOCODE_GENERATION, PSEUDOCODE_REVISION, CODE_GENERATION


def run_pipeline(session: Session, on_update: Optional[Callable] = None):
    """
    Run the transformation pipeline for a session.

    This is the core logic that can be wrapped by different adapters
    (Flask server, Durable Functions, Container Apps, etc.)

    Args:
        session: The transformation session
        on_update: Optional callback when session state changes
    """
    def notify():
        if on_update:
            on_update(session)

    try:
        session.status = Status.RUNNING
        notify()

        # Phase 1: Load and profile data
        session.phase = Phase.PROFILING
        session.log("agent", "Loading MAF transaction data...")
        notify()

        df = read_transactions()
        profile = profile_data(df)
        sample = sample_data(df)

        session.log("agent", f"Loaded {profile['row_count']} rows, {profile['column_count']} columns")

        # Load mapping dictionary
        session.log("agent", "Loading DNAV mapping dictionary...")
        mapping = read_mapping()

        # Phase 2: Generate pseudocode
        session.phase = Phase.PSEUDOCODE_REVIEW
        session.log("agent", "Generating transformation pseudocode...")
        notify()

        user_context = json.dumps({
            "data_profile": profile,
            "sample_rows": sample["sample_rows"][:10],
            "mapping_sheets": list(mapping.keys()),
        }, indent=2, default=str)

        pseudocode_str = chat(PSEUDOCODE_GENERATION, user_context, json_mode=True)
        session.pseudocode = extract_json(pseudocode_str)
        session.pseudocode_version = session.pseudocode.get("version", 1)

        # Log the structured pseudocode for the UI
        session.log("agent", json.dumps(session.pseudocode))

        # Wait for review
        session.awaiting_review = True
        notify()

        # Block until review is submitted
        _wait_for_review(session)

        # Handle review loop
        while not session.review_response.get("approved", False):
            feedback = session.review_response.get("feedback", "")
            session.log("auditor", f"Feedback: {feedback}")

            # Revise pseudocode
            session.log("agent", "Revising pseudocode based on feedback...")
            notify()

            revision_prompt = PSEUDOCODE_REVISION.format(
                feedback=feedback,
                pseudocode=json.dumps(session.pseudocode, indent=2)
            )
            revised_str = chat(revision_prompt, "Please provide the revised pseudocode.", json_mode=True)
            session.pseudocode = extract_json(revised_str)
            session.pseudocode_version = session.pseudocode.get("version", session.pseudocode_version + 1)

            session.log("agent", json.dumps(session.pseudocode))

            # Wait for next review
            session.review_response = None
            session.awaiting_review = True
            notify()
            _wait_for_review(session)

        session.log("auditor", "Approved")
        session.awaiting_review = False

        # Phase 3: Generate code
        session.phase = Phase.CODE_GENERATION
        session.log("agent", "Generating PySpark code...")
        notify()

        code_prompt = CODE_GENERATION.format(
            input_path="input_data/Effective_Transactions_sample.csv",
            output_path="output/maf_fund_transactions.parquet",
            source_columns=", ".join(sample["columns"][:30]),
            pseudocode=json.dumps(session.pseudocode, indent=2)
        )
        session.pyspark_code = chat(code_prompt, "Generate the PySpark code.")

        session.log("agent", f"Generated PySpark code ({len(session.pyspark_code)} chars)")
        session.log("agent", "```python\n" + session.pyspark_code[:2000] + "\n...\n```")

        # Phase 4: Output review
        session.phase = Phase.OUTPUT_REVIEW
        session.log("agent", "Transformation code ready for review.")
        session.awaiting_review = True
        notify()

        _wait_for_review(session)

        if session.review_response.get("approved", False):
            session.log("auditor", "Approved")
            session.phase = Phase.COMPLETED
            session.status = Status.COMPLETED
            session.log("agent", "Transformation complete!")
        else:
            # For now, just complete - could loop back to pseudocode
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


def _wait_for_review(session: Session):
    """Block until a review is submitted."""
    session.review_event = threading.Event()
    session.review_event.wait()  # Blocks until set
    session.review_event = None


def submit_review(session: Session, approved: bool, feedback: str = ""):
    """Submit a review for a session."""
    session.review_response = {"approved": approved, "feedback": feedback}
    if session.review_event:
        session.review_event.set()  # Unblock the pipeline


def start_pipeline_async(session: Session, on_update: Optional[Callable] = None):
    """Start the pipeline in a background thread."""
    thread = threading.Thread(target=run_pipeline, args=(session, on_update))
    thread.daemon = True
    thread.start()
    return thread
