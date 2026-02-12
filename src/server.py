"""Simple HTTP server for frontend - wraps core pipeline."""

from flask import Flask, request, jsonify
from flask_cors import CORS

from core.state import store, Status
from core.pipeline import start_pipeline_async, submit_review

app = Flask(__name__)
CORS(app)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})


@app.route("/api/transform", methods=["POST"])
def start_transform():
    """Start a new transformation session."""
    session = store.create()
    start_pipeline_async(session)
    return jsonify({
        "instance_id": session.id,
        "client_id": "MAF"
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
    """Get session messages."""
    session = store.get(session_id)
    if not session:
        return jsonify({"error": "Not found"}), 404

    messages = [
        {
            "id": msg.id,
            "thread_id": session.id,
            "client_id": "MAF",
            "role": msg.role,
            "content": msg.content,
            "phase": msg.phase,
            "timestamp": msg.timestamp,
        }
        for msg in session.messages
    ]
    return jsonify(messages)


@app.route("/api/transform/<session_id>/review", methods=["POST"])
def post_review(session_id: str):
    """Submit a review."""
    session = store.get(session_id)
    if not session:
        return jsonify({"error": "Not found"}), 404

    data = request.json or {}
    approved = data.get("approved", False)
    feedback = data.get("feedback", "")

    submit_review(session, approved, feedback)

    return jsonify({"status": "review submitted", "approved": approved})


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("MAF Transformation Server")
    print("=" * 50)
    print("Backend:  http://localhost:7071")
    print("Frontend: http://localhost:3000 (run separately)")
    print("=" * 50 + "\n")

    app.run(host="0.0.0.0", port=7071, debug=True)
