"use client";

import { useState, useCallback } from "react";
import {
  StructuredPseudocode,
  Message,
  StepComment as StepCommentType,
  getStepStats,
} from "@/lib/api";
import StepCard from "./StepCard";
import VersionHistory from "./VersionHistory";

interface Props {
  pseudocode: StructuredPseudocode;
  messages: Message[];
  onApprove: () => void;
  onReject: (feedback: string, stepComments: StepCommentType[]) => void;
  disabled?: boolean;
}

export default function PseudocodeReview({
  pseudocode,
  messages,
  onApprove,
  onReject,
  disabled = false,
}: Props) {
  const [stepComments, setStepComments] = useState<Record<string, string>>({});
  const [generalFeedback, setGeneralFeedback] = useState("");
  const [showRejectForm, setShowRejectForm] = useState(false);

  const stats = getStepStats(pseudocode);
  const hasComments = Object.keys(stepComments).length > 0;

  const handleStepComment = useCallback((stepId: string, comment: string) => {
    setStepComments((prev) => {
      if (!comment) {
        const { [stepId]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [stepId]: comment };
    });
  }, []);

  function handleRequestChanges() {
    if (!showRejectForm) {
      setShowRejectForm(true);
      return;
    }

    const comments: StepCommentType[] = Object.entries(stepComments).map(
      ([stepId, comment]) => ({ stepId, comment })
    );

    onReject(generalFeedback, comments);
    setShowRejectForm(false);
    setGeneralFeedback("");
  }

  function handleApprove() {
    if (hasComments) {
      // If there are step comments but user approves, warn them
      if (
        !confirm(
          "You have unsent feedback comments. Approve anyway? (Comments will be discarded)"
        )
      ) {
        return;
      }
    }
    onApprove();
  }

  // Fallback for non-structured pseudocode
  if (!pseudocode.steps || pseudocode.steps.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Transformation Review
        </h2>
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <pre className="text-sm text-gray-700 whitespace-pre-wrap">
            {pseudocode.raw_text || pseudocode.summary}
          </pre>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleApprove}
            disabled={disabled}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            Approve & Generate Code
          </button>
          <button
            onClick={() => setShowRejectForm(true)}
            disabled={disabled}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            Request Changes
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Version History */}
      <VersionHistory messages={messages} />

      {/* Summary Card */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100 p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          {pseudocode.summary}
        </h2>
        <div className="flex gap-4 text-sm text-gray-600">
          <span>
            <span className="font-medium">{stats.fieldMappings}</span> field
            mappings
          </span>
          <span>
            <span className="font-medium">{stats.lookups}</span> lookups
          </span>
          <span>
            <span className="font-medium">{stats.businessRules}</span> business
            rules
          </span>
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {pseudocode.steps.map((step) => (
          <StepCard
            key={step.id}
            step={step}
            onComment={handleStepComment}
            existingComment={stepComments[step.id]}
          />
        ))}
      </div>

      {/* Feedback Section (when requesting changes) */}
      {showRejectForm && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-yellow-800 mb-2">
            Request Changes
          </h3>

          {hasComments && (
            <div className="mb-3 p-3 bg-white rounded border border-yellow-100">
              <p className="text-xs font-medium text-gray-600 mb-2">
                Step-specific comments ({Object.keys(stepComments).length}):
              </p>
              <ul className="text-sm text-gray-700 space-y-1">
                {Object.entries(stepComments).map(([stepId, comment]) => (
                  <li key={stepId}>
                    <span className="font-medium">Step {stepId}:</span> {comment}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <textarea
            value={generalFeedback}
            onChange={(e) => setGeneralFeedback(e.target.value)}
            placeholder="Add any general feedback (optional if you have step comments)..."
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500"
            rows={3}
          />
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-2 border-t border-gray-200">
        <div className="text-sm text-gray-500">
          {hasComments && (
            <span className="flex items-center gap-1">
              <svg
                className="w-4 h-4 text-yellow-600"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
              {Object.keys(stepComments).length} pending comment
              {Object.keys(stepComments).length > 1 ? "s" : ""}
            </span>
          )}
        </div>

        <div className="flex gap-3">
          {showRejectForm && (
            <button
              onClick={() => {
                setShowRejectForm(false);
                setGeneralFeedback("");
              }}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
          )}
          <button
            onClick={handleRequestChanges}
            disabled={
              disabled || (showRejectForm && !hasComments && !generalFeedback)
            }
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            {showRejectForm ? "Submit Feedback" : "Request Changes"}
          </button>
          <button
            onClick={handleApprove}
            disabled={disabled}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
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
                d="M5 13l4 4L19 7"
              />
            </svg>
            Approve & Generate Code
          </button>
        </div>
      </div>
    </div>
  );
}
