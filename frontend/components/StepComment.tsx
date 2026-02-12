"use client";

import { useState } from "react";

interface Props {
  stepId: string;
  onComment: (stepId: string, comment: string) => void;
  existingComment?: string;
}

export default function StepComment({
  stepId,
  onComment,
  existingComment,
}: Props) {
  const [isEditing, setIsEditing] = useState(false);
  const [comment, setComment] = useState(existingComment || "");

  function handleSave() {
    if (comment.trim()) {
      onComment(stepId, comment.trim());
    }
    setIsEditing(false);
  }

  function handleCancel() {
    setComment(existingComment || "");
    setIsEditing(false);
  }

  if (existingComment && !isEditing) {
    return (
      <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-2">
            <span className="text-yellow-600 text-sm">Your comment:</span>
            <p className="text-sm text-gray-700">{existingComment}</p>
          </div>
          <button
            onClick={() => setIsEditing(true)}
            className="text-xs text-gray-500 hover:text-gray-700"
          >
            Edit
          </button>
        </div>
      </div>
    );
  }

  if (isEditing) {
    return (
      <div className="mt-3 p-3 bg-gray-50 border border-gray-200 rounded-lg">
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Add your feedback for this step..."
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          rows={2}
          autoFocus
        />
        <div className="flex gap-2 mt-2">
          <button
            onClick={handleSave}
            disabled={!comment.trim()}
            className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            Save Comment
          </button>
          <button
            onClick={handleCancel}
            className="px-3 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <button
      onClick={() => setIsEditing(true)}
      className="mt-3 flex items-center gap-1.5 text-xs text-gray-500 hover:text-blue-600 transition-colors"
    >
      <svg
        className="w-4 h-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
        />
      </svg>
      Add Comment
    </button>
  );
}
