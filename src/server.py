"""HTTP server exposing MAF workflow for frontend."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify
from flask_cors import CORS

from agents.workflow import store, start_workflow_async, Status

app = Flask(__name__)
CORS(app)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})


@app.route("/api/transform", methods=["POST"])
def start_transform():
    """Start a new transformation session."""
    session = store.create()
    start_workflow_async(session)
    return jsonify({
        "instance_id": session.id,
        "client_id": "MAF_Fund_Transactions",
    }), 202


@app.route("/api/transform/<session_id>/status", methods=["GET"])
def get_status(session_id: str):
    """Get session status."""
    session = store.get(session_id)
    if not session:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "instance_id": session.id,
        "runtime_status": session.status.value,
        "phase": session.phase.value,
        "awaiting_review": session.awaiting_review,
    })


@app.route("/api/transform/<session_id>/messages", methods=["GET"])
def get_messages(session_id: str):
    """Get session messages for chat UI."""
    session = store.get(session_id)
    if not session:
        return jsonify({"error": "Not found"}), 404

    messages = [
        {
            "id": msg.id,
            "thread_id": session.id,
            "client_id": "MAF_Fund_Transactions",
            "role": msg.role,
            "content": msg.content,
            "phase": msg.phase,
            "timestamp": msg.timestamp,
        }
        for msg in session.messages
    ]
    return jsonify(messages)


@app.route("/api/transform/<session_id>/review", methods=["POST"])
def submit_review(session_id: str):
    """Submit auditor review (approve/reject with feedback)."""
    session = store.get(session_id)
    if not session:
        return jsonify({"error": "Not found"}), 404

    data = request.json or {}
    approved = data.get("approved", False)
    feedback = data.get("feedback", "")

    session.submit_review(approved, feedback)

    return jsonify({"status": "review submitted", "approved": approved})


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Fund Transactions Server")
    print("=" * 60)
    print("Backend:  http://localhost:7071")
    print("Frontend: http://localhost:3000")
    print("=" * 60 + "\n")

    app.run(host="0.0.0.0", port=7071, debug=True, use_reloader=False)
