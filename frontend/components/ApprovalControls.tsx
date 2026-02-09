"use client";

import { useState } from "react";

interface Props {
  onApprove: () => void;
  onReject: (feedback: string) => void;
  disabled?: boolean;
}

export default function ApprovalControls({
  onApprove,
  onReject,
  disabled = false,
}: Props) {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");

  function handleReject() {
    if (!showFeedback) {
      setShowFeedback(true);
      return;
    }
    if (!feedback.trim()) return;
    onReject(feedback.trim());
    setShowFeedback(false);
    setFeedback("");
  }

  return (
    <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
      <p className="text-sm font-medium text-yellow-800 mb-3">
        Review required — please approve or provide feedback.
      </p>
      <div className="flex gap-2">
        <button
          onClick={onApprove}
          disabled={disabled}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          Approve
        </button>
        <button
          onClick={handleReject}
          disabled={disabled}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
        >
          {showFeedback ? "Submit Feedback" : "Reject"}
        </button>
      </div>
      {showFeedback && (
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="Describe what needs to change..."
          className="mt-3 w-full px-3 py-2 border rounded-lg text-sm"
          rows={3}
        />
      )}
    </div>
  );
}
